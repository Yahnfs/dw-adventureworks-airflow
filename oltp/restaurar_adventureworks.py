"""Prepara a origem OLTP: baixa o backup oficial e restaura o AdventureWorks2022.

Executado pelo servico ``oltp-restaurar`` do Compose. E idempotente: se a base
ja existir, termina sem fazer nada, preservando o que tiver sido alterado nela.
"""

from __future__ import annotations

import os
import time
import urllib.request
from pathlib import Path

import pyodbc

URL_BACKUP = (
    "https://github.com/Microsoft/sql-server-samples/releases/download/"
    "adventureworks/AdventureWorks2022.bak"
)
ARQUIVO_LOCAL = Path("/backup/AdventureWorks2022.bak")
ARQUIVO_NO_SERVIDOR = "/var/opt/mssql/backup/AdventureWorks2022.bak"
DIR_DADOS = "/var/opt/mssql/data"
BANCO = "AdventureWorks2022"

CONEXAO = (
    "DRIVER={ODBC Driver 18 for SQL Server};SERVER=oltp-mssql,1433;"
    f"UID=sa;PWD={os.environ['OLTP_SA_PASSWORD']};Encrypt=no;"
)


def conectar(tentativas: int = 30) -> pyodbc.Connection:
    for tentativa in range(1, tentativas + 1):
        try:
            return pyodbc.connect(CONEXAO, autocommit=True, timeout=10)
        except pyodbc.Error as erro:
            if tentativa == tentativas:
                raise
            print(f"Aguardando o SQL Server ({tentativa}/{tentativas}): {erro}")
            time.sleep(5)
    raise RuntimeError("Nao foi possivel conectar ao SQL Server.")


def baixar_backup() -> None:
    if ARQUIVO_LOCAL.exists() and ARQUIVO_LOCAL.stat().st_size > 0:
        print(f"Backup ja disponivel em {ARQUIVO_LOCAL}.")
        return
    print(f"Baixando {URL_BACKUP}")
    temporario = ARQUIVO_LOCAL.with_suffix(".parcial")
    urllib.request.urlretrieve(URL_BACKUP, temporario)
    temporario.rename(ARQUIVO_LOCAL)
    print(f"Backup salvo com {ARQUIVO_LOCAL.stat().st_size:,} bytes.")


def restaurar(conexao: pyodbc.Connection) -> None:
    cursor = conexao.cursor()
    cursor.execute(f"RESTORE FILELISTONLY FROM DISK = N'{ARQUIVO_NO_SERVIDOR}';")
    arquivos = [(linha.LogicalName, linha.Type) for linha in cursor.fetchall()]

    movimentos = ", ".join(
        f"MOVE N'{nome}' TO N'{DIR_DADOS}/{nome}{'.ldf' if tipo == 'L' else '.mdf'}'"
        for nome, tipo in arquivos
    )
    cursor.execute(
        f"RESTORE DATABASE [{BANCO}] FROM DISK = N'{ARQUIVO_NO_SERVIDOR}' "
        f"WITH {movimentos}, RECOVERY, STATS = 25;"
    )
    # O RESTORE devolve varios conjuntos de mensagens e so termina depois que
    # todos sao consumidos.
    while cursor.nextset():
        pass


def main() -> None:
    conexao = conectar()
    existente = conexao.execute(
        "SELECT COUNT(*) FROM sys.databases WHERE name = ?;", BANCO
    ).fetchval()
    if existente:
        print(f"Base {BANCO} ja restaurada; nada a fazer.")
        return

    baixar_backup()
    restaurar(conexao)
    pedidos = conexao.execute(
        f"SELECT COUNT(*) FROM [{BANCO}].Sales.SalesOrderDetail;"
    ).fetchval()
    print(f"Base {BANCO} restaurada: {pedidos} itens de pedido.")


if __name__ == "__main__":
    main()
