"""Ativos (Assets) que ligam as DAGs por dados, e nao por horario."""

from __future__ import annotations

from airflow.sdk import Asset

DW_ATUALIZADO = Asset("dw_adventureworks_atualizado")
