"""Controle da carga incremental: marcas d'agua e log de execucao.

Estrategia adotada (captura de mudancas por coluna de auditoria):

1. Antes de extrair uma entidade, a ETL le em ``meta.etl_controle`` a maior
   ``ModifiedDate`` ja processada com sucesso (a marca d'agua).
2. Extrai do OLTP somente as linhas com ``ModifiedDate`` maior que a marca.
3. Aplica os dados no DW por operacoes idempotentes (``INSERT ... ON CONFLICT
   DO UPDATE``), de modo que reprocessar a mesma janela nao duplica registros.
4. A marca avanca na mesma transacao que grava os dados. Se a carga falhar, a
   marca fica onde estava e o proximo ciclo reprocessa a janela pendente.

Um commit tardio na origem, com ``ModifiedDate`` anterior a marca, nao seria
visto pelo filtro. A tarefa ``validar_carga`` cobre esse risco para insercoes,
conferindo contagens e somas entre origem e destino ao final de cada ciclo.
"""

from __future__ import annotations

from datetime import datetime

import psycopg

MARCA_INICIAL = datetime(1900, 1, 1)


def obter_marca(conexao: psycopg.Connection, entidade: str) -> datetime:
    """Le a marca d'agua da entidade."""
    linha = conexao.execute(
        "SELECT dt_ultima_carga FROM meta.etl_controle WHERE nm_entidade = %s;",
        (entidade,),
    ).fetchone()

    if linha is None:
        raise ValueError(
            f"Entidade '{entidade}' nao registrada em meta.etl_controle. "
            "Execute o script sql/01_ddl_dw.sql."
        )
    return linha[0]


def avancar_marca(
    conexao: psycopg.Connection,
    entidade: str,
    nova_marca: datetime,
    qt_registros: int,
) -> None:
    """Grava a nova marca d'agua, na mesma transacao da carga da entidade.

    A marca nunca retrocede: ``GREATEST`` impede que um reprocessamento manual
    de um lote antigo invalide o avanco de execucoes anteriores.
    """
    conexao.execute(
        """
        UPDATE meta.etl_controle
           SET dt_ultima_carga     = GREATEST(dt_ultima_carga, %s),
               qt_registros_ultima = %s,
               qt_registros_total  = qt_registros_total + %s,
               dt_atualizacao      = CURRENT_TIMESTAMP
         WHERE nm_entidade = %s;
        """,
        (nova_marca, qt_registros, qt_registros, entidade),
    )


def registrar_inicio(
    conexao: psycopg.Connection,
    id_lote: str,
    entidade: str,
    fase: str,
    marca: datetime,
) -> int:
    """Abre uma linha de auditoria em ``meta.etl_execucao``."""
    return conexao.execute(
        """
        INSERT INTO meta.etl_execucao
            (id_lote, nm_entidade, ds_fase, dt_inicio, ds_marca_agua_de, ds_status)
        VALUES (%s, %s, %s, CURRENT_TIMESTAMP, %s, 'EM_EXECUCAO')
        RETURNING id_execucao;
        """,
        (id_lote, entidade, fase, marca),
    ).fetchone()[0]


def registrar_fim(
    conexao: psycopg.Connection,
    id_execucao: int,
    *,
    extraidos: int = 0,
    inseridos: int = 0,
    atualizados: int = 0,
    marca_ate: datetime | None = None,
    status: str = "SUCESSO",
    mensagem: str | None = None,
) -> None:
    """Fecha a linha de auditoria com o resultado da carga."""
    conexao.execute(
        """
        UPDATE meta.etl_execucao
           SET dt_fim            = CURRENT_TIMESTAMP,
               qt_extraidos      = %s,
               qt_inseridos      = %s,
               qt_atualizados    = %s,
               ds_marca_agua_ate = %s,
               ds_status         = %s,
               ds_mensagem       = %s
         WHERE id_execucao = %s;
        """,
        (extraidos, inseridos, atualizados, marca_ate, status, mensagem, id_execucao),
    )


def reiniciar_marcas(conexao: psycopg.Connection) -> None:
    """Zera todas as marcas d'agua, forcando uma recarga completa no ciclo."""
    conexao.execute(
        """
        UPDATE meta.etl_controle
           SET dt_ultima_carga     = %s,
               qt_registros_ultima = 0,
               dt_atualizacao      = CURRENT_TIMESTAMP;
        """,
        (MARCA_INICIAL,),
    )
