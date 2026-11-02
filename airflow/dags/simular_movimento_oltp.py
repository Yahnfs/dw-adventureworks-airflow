"""Comprovacao do comportamento incremental.

Disparo manual. Aplica na origem o script sql/98_simular_alteracoes.sql, que
provoca cinco eventos conhecidos, e em seguida dispara a ETL. O resultado pode
ser conferido em meta.etl_execucao e em sql/99_validacao.sql.
"""

from __future__ import annotations

import re
from pathlib import Path

import pendulum
from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.sdk import DAG, task

from aw_etl.conexoes import conexao_origem

SCRIPT = Path("/opt/airflow/sql/98_simular_alteracoes.sql")


@task
def aplicar_movimento():
    # GO e separador de lotes do sqlcmd, e nao um comando do SQL Server.
    lotes = re.split(r"^GO\s*$", SCRIPT.read_text(encoding="utf-8"), flags=re.MULTILINE)
    with conexao_origem(autocommit=True) as origem:
        cursor = origem.cursor()
        for lote in filter(str.strip, lotes):
            cursor.execute(lote)
            while cursor.nextset():
                pass


with DAG(
    dag_id="simular_movimento_oltp",
    description="Gera movimento conhecido na origem e dispara a ETL incremental",
    doc_md=__doc__,
    schedule=None,
    start_date=pendulum.datetime(2026, 11, 1, tz="America/Sao_Paulo"),
    catchup=False,
    max_active_runs=1,
    default_args={"owner": "yahn"},
    tags=["adventureworks", "demonstracao"],
) as dag:
    aplicar_movimento() >> TriggerDagRunOperator(
        task_id="disparar_etl",
        trigger_dag_id="etl_adventureworks_incremental",
    )
