"""Gera docs/dicionario_dados.md a partir do catalogo do PostgreSQL.

    python docs/gerar_dicionario.py

Le as descricoes registradas com COMMENT ON (sql/01_ddl_dw.sql e
sql/02_comentarios.sql), de modo que o dicionario nunca diverge do banco
implantado. Requer ``psycopg`` e o conteiner dw-postgres em execucao.
"""

from __future__ import annotations

from pathlib import Path

import psycopg

SAIDA = Path(__file__).resolve().parent / "dicionario_dados.md"
CONEXAO = "host=localhost port=5434 dbname=dw_adventureworks user=dw_user password=dw_pass"

CABECALHO = """# Dicionario de dados - Data Warehouse AdventureWorks

> Gerado por `docs/gerar_dicionario.py` a partir do catalogo do PostgreSQL.

## Convencoes de nomenclatura

| Prefixo | Significado | Exemplo |
|---|---|---|
| `sk_` | chave substituta gerada pelo DW | `sk_produto` |
| `id_` | chave natural herdada da origem | `id_produto` |
| `cd_` | codigo alfanumerico de negocio | `cd_produto` |
| `nm_` | nome ou descritor curto | `nm_categoria` |
| `ds_` | descricao textual | `ds_cargo` |
| `tp_` | tipo ou classificacao | `tp_cliente` |
| `dt_` | data ou data e hora | `dt_pedido` |
| `vl_` | valor monetario, em dolares americanos (US$) | `vl_liquido` |
| `qt_` | quantidade | `qt_vendida` |
| `pc_` | percentual | `pc_desconto_unitario` |
| `nr_` | numero sequencial ou ordinal | `nr_versao` |
| `fl_` | indicador logico | `fl_corrente` |

"""

SQL_TABELAS = """
SELECT c.oid, n.nspname, c.relname, obj_description(c.oid, 'pg_class')
  FROM pg_class AS c
  JOIN pg_namespace AS n ON n.oid = c.relnamespace
 WHERE c.relkind = 'r' AND n.nspname = %s
 ORDER BY CASE WHEN c.relname LIKE 'fato%%' THEN 0 ELSE 1 END, c.relname;
"""

SQL_COLUNAS = """
SELECT a.attname,
       format_type(a.atttypid, a.atttypmod),
       a.attnotnull,
       col_description(a.attrelid, a.attnum),
       (SELECT string_agg(
                   CASE ct.contype WHEN 'p' THEN 'PK'
                        ELSE 'FK -> ' || ct.confrelid::regclass::text END, ', ')
          FROM pg_constraint AS ct
         WHERE ct.conrelid = a.attrelid
           AND ct.contype IN ('p', 'f')
           AND a.attnum = ANY (ct.conkey))
  FROM pg_attribute AS a
 WHERE a.attrelid = %s AND a.attnum > 0 AND NOT a.attisdropped
 ORDER BY a.attnum;
"""


def secao(conexao: psycopg.Connection, esquema: str, titulo: str) -> list[str]:
    linhas = [f"\n## {titulo}\n"]
    for oid, nome_esquema, tabela, descricao in conexao.execute(SQL_TABELAS, (esquema,)).fetchall():
        qualificada = f"{nome_esquema}.{tabela}"
        total = conexao.execute(f"SELECT count(*) FROM {qualificada};").fetchone()[0]
        linhas.append(f"### `{qualificada}`\n")
        linhas.append(f"{descricao or 'Sem descricao registrada.'}\n")
        linhas.append(f"**Linhas carregadas:** {total:,}\n".replace(",", "."))
        linhas.append("| Coluna | Tipo | Nulo | Chave | Descricao |")
        linhas.append("|---|---|---|---|---|")
        for coluna, tipo, nao_nulo, comentario, chave in conexao.execute(SQL_COLUNAS, (oid,)).fetchall():
            texto = (comentario or "").replace("|", "\\|")
            linhas.append(
                f"| `{coluna}` | {tipo} | {'nao' if nao_nulo else 'sim'} | {chave or ''} | {texto} |"
            )
        linhas.append("")
    return linhas


def main() -> None:
    with psycopg.connect(CONEXAO) as conexao:
        corpo = secao(conexao, "dw", "Camada dimensional (`dw`)")
        corpo += secao(conexao, "meta", "Metadados de controle (`meta`)")
    SAIDA.write_text(CABECALHO + "\n".join(corpo), encoding="utf-8")
    print(f"Dicionario salvo em {SAIDA}")


if __name__ == "__main__":
    main()
