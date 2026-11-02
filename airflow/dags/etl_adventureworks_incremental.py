"""ETL incremental do Data Warehouse AdventureWorks.

Fluxo: verifica o ambiente, prepara o lote, gera o calendario, carrega as oito
dimensoes em paralelo e depois as duas fatos, valida a carga contra a origem e,
se algo foi gravado, publica o ativo que dispara o calculo dos indicadores.

As dimensoes precedem as fatos porque a busca das chaves substitutas depende
delas. Cada entidade tem seu proprio grupo extrair >> transformar. Quando nao
ha novidade, o grupo inteiro termina como skipped e nada e escrito no DW.
"""

from __future__ import annotations

from datetime import timedelta

import pendulum
from airflow.sdk import DAG, Param, TaskGroup, task
from airflow.task.trigger_rule import TriggerRule

from aw_etl import tarefas
from aw_etl.ativos import DW_ATUALIZADO
from aw_etl.consultas_origem import DIMENSOES, FATOS


# Muitas retentativas: na primeira subida do ambiente, a restauracao da origem
# ainda pode estar em andamento quando o ciclo agendado comeca.
@task(retries=10)
def verificar_ambiente():
    tarefas.verificar_ambiente()


@task
def preparar_lote(params=None):
    tarefas.preparar_lote(params["recarga_completa"])


@task
def carregar_dim_tempo():
    return tarefas.carregar_dim_tempo()


@task
def extrair(entidade: str, run_id=None):
    return tarefas.extrair(entidade, run_id)


@task
def transformar(entidade: str, extracao: dict):
    return tarefas.transformar(entidade, extracao)


@task(trigger_rule=TriggerRule.NONE_FAILED)
def validar_carga(run_id=None):
    tarefas.validar_carga(run_id)


@task.short_circuit
def houve_alteracao(run_id=None):
    return tarefas.houve_alteracao(run_id)


@task(outlets=[DW_ATUALIZADO])
def atualizar_estatisticas():
    tarefas.atualizar_estatisticas()


def grupo_entidade(entidade: str, regra_inicio: TriggerRule) -> TaskGroup:
    """Cria o grupo extrair >> transformar de uma entidade."""
    with TaskGroup(group_id=entidade) as grupo:
        extracao = extrair.override(task_id="extrair", trigger_rule=regra_inicio)(entidade)
        transformar.override(task_id="transformar")(entidade, extracao)
    return grupo


with DAG(
    dag_id="etl_adventureworks_incremental",
    description="Carga incremental do DW AdventureWorks (SQL Server -> PostgreSQL)",
    doc_md=__doc__,
    schedule="0 2 * * *",
    start_date=pendulum.datetime(2026, 11, 1, tz="America/Sao_Paulo"),
    catchup=False,
    max_active_runs=1,
    default_args={"owner": "yahn", "retries": 2, "retry_delay": timedelta(seconds=30)},
    params={
        "recarga_completa": Param(
            False,
            type="boolean",
            description="Zera as marcas d'agua e recarrega todas as entidades.",
        )
    },
    tags=["adventureworks", "etl", "incremental"],
) as dag:
    with TaskGroup(group_id="dimensoes") as dimensoes:
        for entidade in DIMENSOES:
            grupo_entidade(entidade, TriggerRule.ALL_SUCCESS)

    # NONE_FAILED: a carga das fatos segue mesmo com todas as dimensoes skipped.
    with TaskGroup(group_id="fatos") as fatos:
        for entidade in FATOS:
            grupo_entidade(entidade, TriggerRule.NONE_FAILED)

    (
        verificar_ambiente()
        >> preparar_lote()
        >> carregar_dim_tempo()
        >> dimensoes
        >> fatos
        >> validar_carga()
        >> houve_alteracao()
        >> atualizar_estatisticas()
    )
