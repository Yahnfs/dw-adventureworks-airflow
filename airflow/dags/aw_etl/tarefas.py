"""Funcoes executadas pelas tasks da DAG ``etl_adventureworks_incremental``.

Cada entidade passa por duas tasks, separadas de proposito:

    extrair     le o recorte incremental do OLTP e o grava em ``stg`` (COPY)
    transformar promove ``stg`` para ``dw`` e avanca a marca d'agua, na mesma
                transacao

Como o staging ja esta confirmado quando a transformacao comeca, uma falha em
``transformar`` e reexecutada sem voltar ao OLTP. Se a extracao nao trouxer
linhas, a task termina como *skipped* e o Airflow pula a transformacao, de modo
que um ciclo sem novidade aparece na interface sem nenhuma escrita no DW.
"""

from __future__ import annotations

import logging
from datetime import date, datetime

import psycopg
from airflow.sdk.exceptions import AirflowSkipException

from aw_etl import controle, dimensao_tempo, transformacoes
from aw_etl.conexoes import conexao_destino, conexao_origem
from aw_etl.consultas_origem import CATALOGO_EXTRACAO, consulta_extracao

logger = logging.getLogger(__name__)

TAMANHO_LOTE = 20_000
TOLERANCIA_VALOR = 1.00

# As contagens da origem usam o mesmo universo carregado no DW. No destino,
# dim_produto conta produtos, e nao versoes, e os membros -1 ficam de fora.
CONFERENCIAS: tuple[tuple[str, str, str], ...] = (
    ("Linhas de fato_vendas",
     "SELECT COUNT(*) FROM Sales.SalesOrderDetail;",
     "SELECT COUNT(*) FROM dw.fato_vendas;"),
    ("Linhas de fato_compras",
     "SELECT COUNT(*) FROM Purchasing.PurchaseOrderDetail;",
     "SELECT COUNT(*) FROM dw.fato_compras;"),
    ("Linhas de dim_cliente",
     "SELECT COUNT(*) FROM Sales.Customer;",
     "SELECT COUNT(*) FROM dw.dim_cliente WHERE sk_cliente > 0;"),
    ("Produtos distintos em dim_produto",
     "SELECT COUNT(*) FROM Production.Product;",
     "SELECT COUNT(DISTINCT id_produto) FROM dw.dim_produto WHERE id_produto > 0;"),
    ("Linhas de dim_funcionario",
     "SELECT COUNT(*) FROM HumanResources.Employee;",
     "SELECT COUNT(*) FROM dw.dim_funcionario WHERE sk_funcionario > 0;"),
    ("Linhas de dim_geografia",
     "SELECT COUNT(*) FROM Person.Address;",
     "SELECT COUNT(*) FROM dw.dim_geografia WHERE sk_geografia > 0;"),
    ("Linhas de dim_fornecedor",
     "SELECT COUNT(*) FROM Purchasing.Vendor;",
     "SELECT COUNT(*) FROM dw.dim_fornecedor WHERE sk_fornecedor > 0;"),
    ("Receita liquida (soma)",
     "SELECT SUM(LineTotal) FROM Sales.SalesOrderDetail;",
     "SELECT SUM(vl_liquido) FROM dw.fato_vendas;"),
    ("Valor comprado (soma)",
     "SELECT SUM(LineTotal) FROM Purchasing.PurchaseOrderDetail;",
     "SELECT SUM(vl_total_linha) FROM dw.fato_compras;"),
)

# Cada consulta conta violacoes: o valor esperado e sempre zero.
TESTES_INTEGRIDADE: tuple[tuple[str, str], ...] = (
    ("fato_vendas: item duplicado",
     "SELECT COUNT(*) FROM (SELECT id_item_venda FROM dw.fato_vendas "
     "GROUP BY id_item_venda HAVING COUNT(*) > 1) AS d;"),
    ("fato_compras: item duplicado",
     "SELECT COUNT(*) FROM (SELECT id_item_compra FROM dw.fato_compras "
     "GROUP BY id_item_compra HAVING COUNT(*) > 1) AS d;"),
    ("fato_vendas: liquido diferente de bruto - desconto",
     "SELECT COUNT(*) FROM dw.fato_vendas "
     "WHERE ROUND(vl_bruto - vl_desconto, 2) <> ROUND(vl_liquido, 2);"),
    ("fato_vendas: linha sem produto, cliente ou data do pedido",
     "SELECT COUNT(*) FROM dw.fato_vendas "
     "WHERE sk_produto = -1 OR sk_cliente = -1 OR sk_tempo_pedido = -1;"),
    ("dim_produto: mais de uma versao corrente",
     "SELECT COUNT(*) FROM (SELECT id_produto FROM dw.dim_produto "
     "WHERE fl_corrente GROUP BY id_produto HAVING COUNT(*) > 1) AS d;"),
    ("dim_produto: vigencia invertida",
     "SELECT COUNT(*) FROM dw.dim_produto WHERE dt_fim_validade < dt_inicio_validade;"),
)


def verificar_ambiente() -> None:
    """Falha cedo, e com retentativas, se origem ou destino nao responderem."""
    with conexao_origem() as origem:
        pedidos = origem.execute("SELECT COUNT(*) FROM Sales.SalesOrderHeader;").fetchval()
    with conexao_destino() as dw:
        entidades = dw.execute("SELECT COUNT(*) FROM meta.etl_controle;").fetchone()[0]
    if entidades != len(CATALOGO_EXTRACAO):
        raise ValueError(f"meta.etl_controle tem {entidades} entidades.")
    logger.info("Origem com %d pedidos; destino com %d entidades.", pedidos, entidades)


def preparar_lote(recarga_completa: bool) -> None:
    """Zera as marcas d'agua quando a DAG e disparada em recarga completa."""
    if not recarga_completa:
        return
    with conexao_destino() as dw:
        controle.reiniciar_marcas(dw)
        dw.commit()
    logger.warning("Recarga completa solicitada: marcas d'agua reiniciadas.")


def carregar_dim_tempo() -> int:
    """Gera o calendario, em anos inteiros, cobrindo todas as datas do OLTP."""
    with conexao_origem() as origem, conexao_destino() as dw:
        inicio, fim = dimensao_tempo.intervalo_necessario(origem.cursor())
        novas = dimensao_tempo.carregar(
            dw, date(inicio.year, 1, 1), date(fim.year, 12, 31)
        )
        dw.commit()
    logger.info("dim_tempo: %d datas novas ate %s.", novas, fim.year)
    return novas


def _copiar_para_staging(
    cursor_origem,
    dw: psycopg.Connection,
    entidade: str,
    marca: datetime,
) -> tuple[int, datetime | None]:
    """Copia o recorte incremental para o staging e devolve volume e maior data."""
    tabela_staging = CATALOGO_EXTRACAO[entidade]["staging"]
    dw.execute(f"TRUNCATE TABLE {tabela_staging};")

    cursor_origem.execute(consulta_extracao(entidade), marca)
    colunas = [descricao[0] for descricao in cursor_origem.description]
    indice_modificacao = colunas.index("dt_modificacao_origem")

    total = 0
    maior_marca: datetime | None = None
    comando_copy = f"COPY {tabela_staging} ({', '.join(colunas)}) FROM STDIN"

    with dw.cursor() as cursor_dw, cursor_dw.copy(comando_copy) as copia:
        while lote := cursor_origem.fetchmany(TAMANHO_LOTE):
            for linha in lote:
                copia.write_row(tuple(linha))
            total += len(lote)
            # A consulta vem ordenada pela data de modificacao.
            maior_marca = lote[-1][indice_modificacao]

    return total, maior_marca


def extrair(entidade: str, id_lote: str) -> dict:
    """Extrai a entidade para o staging; sem novidade, termina como skipped."""
    fase = "DIMENSAO" if entidade.startswith("dim_") else "FATO"

    with (
        conexao_destino(autocommit=True) as log,
        conexao_destino() as dw,
        conexao_origem() as origem,
    ):
        marca = controle.obter_marca(dw, entidade)
        id_execucao = controle.registrar_inicio(log, id_lote, entidade, fase, marca)
        try:
            extraidos, maior_marca = _copiar_para_staging(
                origem.cursor(), dw, entidade, marca
            )
            dw.commit()
        except Exception as erro:
            dw.rollback()
            controle.registrar_fim(
                log, id_execucao, status="ERRO",
                mensagem=f"{type(erro).__name__}: {erro}",
            )
            raise

        if extraidos == 0:
            controle.registrar_fim(log, id_execucao, status="SEM_ALTERACAO")
            raise AirflowSkipException(f"{entidade}: nada novo desde {marca}.")

    logger.info("%s: %d linhas em staging (marca %s).", entidade, extraidos, marca)
    return {
        "id_execucao": id_execucao,
        "extraidos": extraidos,
        "marca_ate": maior_marca.isoformat(),
    }


def _contar_resultado(cursor) -> tuple[int, int]:
    """Separa insercoes de atualizacoes a partir do RETURNING (xmax = 0)."""
    if cursor.description is None:
        return 0, 0
    linhas = cursor.fetchall()
    inseridos = sum(1 for linha in linhas if linha[0])
    return inseridos, len(linhas) - inseridos


def _promover(dw: psycopg.Connection, entidade: str) -> tuple[int, int]:
    if entidade == "dim_produto":
        with dw.cursor() as cursor:
            cursor.execute(transformacoes.PRODUTO_SCD2_DETECTAR)
            cursor.execute(transformacoes.PRODUTO_SCD2_ENCERRAR)
            versoes_encerradas = cursor.rowcount
            cursor.execute(transformacoes.PRODUTO_SCD2_INSERIR)
            novas_versoes, _ = _contar_resultado(cursor)
        # No SCD Tipo 2 toda mudanca gera linha nova; as versoes encerradas
        # equivalem as atualizacoes logicas de produtos existentes.
        return novas_versoes - versoes_encerradas, versoes_encerradas

    comando = transformacoes.SCD1.get(entidade) or transformacoes.FATOS.get(entidade)
    if comando is None:
        raise ValueError(f"Nenhuma transformacao definida para '{entidade}'.")
    with dw.cursor() as cursor:
        cursor.execute(comando)
        return _contar_resultado(cursor)


def transformar(entidade: str, extracao: dict) -> dict:
    """Promove o staging para o DW e avanca a marca, na mesma transacao."""
    id_execucao = extracao["id_execucao"]
    extraidos = extracao["extraidos"]
    marca_ate = datetime.fromisoformat(extracao["marca_ate"])

    with conexao_destino(autocommit=True) as log, conexao_destino() as dw:
        try:
            inseridos, atualizados = _promover(dw, entidade)
            controle.avancar_marca(dw, entidade, marca_ate, extraidos)
            dw.commit()
        except Exception as erro:
            dw.rollback()
            controle.registrar_fim(
                log, id_execucao, extraidos=extraidos, status="ERRO",
                mensagem=f"{type(erro).__name__}: {erro}",
            )
            raise

        controle.registrar_fim(
            log, id_execucao, extraidos=extraidos, inseridos=inseridos,
            atualizados=atualizados, marca_ate=marca_ate,
        )

    logger.info(
        "%s: extraidos=%d inseridos=%d atualizados=%d.",
        entidade, extraidos, inseridos, atualizados,
    )
    return {"inseridos": inseridos, "atualizados": atualizados}


def validar_carga(id_lote: str) -> None:
    """Confere origem x destino e a integridade do DW; reprova o ciclo se divergir."""
    resultados: list[tuple[str, float, float, bool]] = []

    with conexao_origem() as origem, conexao_destino() as dw:
        for descricao, sql_origem, sql_destino in CONFERENCIAS:
            valor_origem = float(origem.execute(sql_origem).fetchval() or 0)
            valor_destino = float(dw.execute(sql_destino).fetchone()[0] or 0)
            aprovado = abs(valor_origem - valor_destino) <= TOLERANCIA_VALOR
            resultados.append((descricao, valor_origem, valor_destino, aprovado))

        for descricao, sql_teste in TESTES_INTEGRIDADE:
            violacoes = float(dw.execute(sql_teste).fetchone()[0])
            resultados.append((descricao, 0.0, violacoes, violacoes == 0))

        with dw.cursor() as cursor:
            cursor.executemany(
                """
                INSERT INTO meta.etl_validacao
                    (id_lote, ds_verificacao, vl_origem, vl_destino, fl_aprovado)
                VALUES (%s, %s, %s, %s, %s);
                """,
                [(id_lote, *resultado) for resultado in resultados],
            )
        dw.commit()

    reprovados = [r for r in resultados if not r[3]]
    for descricao, valor_origem, valor_destino, aprovado in resultados:
        logger.info(
            "%-58s origem=%.2f destino=%.2f %s",
            descricao, valor_origem, valor_destino, "OK" if aprovado else "REPROVADO",
        )
    if reprovados:
        raise ValueError(f"Verificacoes reprovadas: {[r[0] for r in reprovados]}")


def houve_alteracao(id_lote: str) -> bool:
    """Indica se o ciclo gravou algo; sem escrita, nao ha o que publicar."""
    with conexao_destino() as dw:
        escritas = dw.execute(
            """
            SELECT COALESCE(SUM(qt_inseridos + qt_atualizados), 0)
              FROM meta.etl_execucao
             WHERE id_lote = %s;
            """,
            (id_lote,),
        ).fetchone()[0]
    logger.info("Ciclo %s gravou %d linhas no DW.", id_lote, escritas)
    return escritas > 0


def atualizar_estatisticas() -> None:
    """Atualiza as estatisticas do planejador apos uma carga com escrita."""
    with conexao_destino(autocommit=True) as dw:
        for tabela in ("dw.dim_produto", "dw.dim_cliente", "dw.fato_vendas", "dw.fato_compras"):
            dw.execute(f"VACUUM ANALYZE {tabela};")
