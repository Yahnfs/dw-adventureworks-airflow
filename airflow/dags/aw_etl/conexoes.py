"""Conexoes com a origem e o destino, a partir das Connections do Airflow.

As credenciais ficam nas variaveis ``AIRFLOW_CONN_*`` do arquivo ``.env``.
Nenhuma credencial e escrita no codigo versionado.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import psycopg
import pyodbc
from airflow.sdk import Connection

ID_ORIGEM = "oltp_mssql"
ID_DESTINO = "dw_postgres"


@contextmanager
def conexao_origem(autocommit: bool = False) -> Iterator[pyodbc.Connection]:
    """Abre uma conexao com o SQL Server (AdventureWorks / OLTP)."""
    dados = Connection.get(ID_ORIGEM)
    conexao = pyodbc.connect(
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={dados.host},{dados.port};DATABASE={dados.schema};"
        f"UID={dados.login};PWD={dados.password};Encrypt=no;",
        autocommit=autocommit,
        timeout=15,
    )
    try:
        yield conexao
    finally:
        conexao.close()


@contextmanager
def conexao_destino(autocommit: bool = False) -> Iterator[psycopg.Connection]:
    """Abre uma conexao com o PostgreSQL (Data Warehouse / OLAP)."""
    dados = Connection.get(ID_DESTINO)
    conexao = psycopg.connect(
        host=dados.host,
        port=dados.port,
        dbname=dados.schema,
        user=dados.login,
        password=dados.password,
        autocommit=autocommit,
    )
    try:
        yield conexao
    finally:
        conexao.close()
