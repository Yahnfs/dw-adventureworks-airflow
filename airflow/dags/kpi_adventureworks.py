"""Calculo dos indicadores do Data Warehouse AdventureWorks.

Nao tem horario proprio: roda quando a ETL publica o ativo de DW atualizado.
Cada task atualiza uma visao materializada do esquema kpi, e a ultima confere
que nenhum indicador ficou vazio.
"""

from __future__ import annotations

from datetime import timedelta

import pendulum
from airflow.providers.common.sql.operators.sql import (
    SQLCheckOperator,
    SQLExecuteQueryOperator,
)
from airflow.sdk import DAG

from aw_etl.ativos import DW_ATUALIZADO
from aw_etl.conexoes import ID_DESTINO

INDICADORES = (
    "mv_receita_liquida",
    "mv_ticket_medio",
    "mv_margem_bruta",
    "mv_taxa_desconto",
    "mv_crescimento_yoy",
    "mv_curva_abc",
    "mv_sazonalidade",
    "mv_recompra",
    "mv_forca_vendas",
    "mv_fornecedores",
)

SQL_CONFERENCIA = "SELECT " + " AND ".join(
    f"EXISTS (SELECT 1 FROM kpi.{indicador})" for indicador in INDICADORES
) + ";"

with DAG(
    dag_id="kpi_adventureworks",
    description="Atualiza as dez visoes de indicadores sobre o modelo estrela",
    doc_md=__doc__,
    schedule=[DW_ATUALIZADO],
    start_date=pendulum.datetime(2026, 11, 1, tz="America/Sao_Paulo"),
    catchup=False,
    max_active_runs=1,
    default_args={"owner": "yahn", "retries": 1, "retry_delay": timedelta(seconds=30)},
    tags=["adventureworks", "kpi"],
) as dag:
    conferir = SQLCheckOperator(
        task_id="conferir_indicadores",
        conn_id=ID_DESTINO,
        sql=SQL_CONFERENCIA,
    )

    for indicador in INDICADORES:
        SQLExecuteQueryOperator(
            task_id=f"atualizar_{indicador.removeprefix('mv_')}",
            conn_id=ID_DESTINO,
            sql=f"REFRESH MATERIALIZED VIEW kpi.{indicador};",
            autocommit=True,
        ) >> conferir
