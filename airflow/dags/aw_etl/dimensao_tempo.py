"""Geracao da dimensao tempo (calendario).

Diferentemente das demais dimensoes, a dimensao tempo nao e extraida do
sistema transacional: ela e gerada proceduralmente a partir de um intervalo de
datas. Sua chave substituta e "inteligente" (formato AAAAMMDD), o que dispensa
uma busca na dimensao durante a carga dos fatos e mantem as consultas
legiveis.

A carga e idempotente: so as datas que faltam sao inseridas. O intervalo e
ampliado automaticamente para cobrir as datas efetivamente presentes no OLTP,
evitando que algum fato precise recorrer ao membro "Nao Informado" por falta
de data correspondente no calendario.
"""

from __future__ import annotations

from datetime import date, timedelta

import psycopg

MESES = [
    "Janeiro", "Fevereiro", "Marco", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]
MESES_ABREV = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
               "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
DIAS_SEMANA = [
    "Segunda-feira", "Terca-feira", "Quarta-feira", "Quinta-feira",
    "Sexta-feira", "Sabado", "Domingo",
]

COLUNAS = (
    "sk_tempo, dt_data, nr_ano, nr_semestre, nr_trimestre, nr_mes, nr_dia, "
    "nr_semana_ano, nr_dia_semana, nr_dia_ano, nm_mes, nm_mes_abrev, "
    "nm_dia_semana, ds_ano_mes, ds_ano_trimestre, fl_fim_semana, "
    "dt_primeiro_dia_mes, dt_ultimo_dia_mes"
)


def _ultimo_dia_do_mes(dia: date) -> date:
    if dia.month == 12:
        return date(dia.year, 12, 31)
    return date(dia.year, dia.month + 1, 1) - timedelta(days=1)


def _linha(dia: date) -> tuple:
    trimestre = (dia.month - 1) // 3 + 1
    indice_dia_semana = dia.weekday()  # 0 = segunda-feira
    return (
        int(dia.strftime("%Y%m%d")),
        dia,
        dia.year,
        1 if dia.month <= 6 else 2,
        trimestre,
        dia.month,
        dia.day,
        int(dia.strftime("%V")),
        indice_dia_semana + 1,
        dia.timetuple().tm_yday,
        MESES[dia.month - 1],
        MESES_ABREV[dia.month - 1],
        DIAS_SEMANA[indice_dia_semana],
        f"{dia.year:04d}-{dia.month:02d}",
        f"{dia.year:04d}-Q{trimestre}",
        indice_dia_semana >= 5,
        date(dia.year, dia.month, 1),
        _ultimo_dia_do_mes(dia),
    )


def carregar(
    conexao: psycopg.Connection, data_inicio: date, data_fim: date
) -> int:
    """Insere na dimensao tempo as datas que faltam. Devolve as linhas novas."""
    marcadores = ", ".join(["%s"] * 18)
    sql = f"INSERT INTO dw.dim_tempo ({COLUNAS}) VALUES ({marcadores});"

    existentes = {
        linha[0] for linha in conexao.execute("SELECT dt_data FROM dw.dim_tempo;")
    }
    linhas = []
    dia = data_inicio
    while dia <= data_fim:
        if dia not in existentes:
            linhas.append(_linha(dia))
        dia += timedelta(days=1)

    if linhas:
        with conexao.cursor() as cursor:
            cursor.executemany(sql, linhas)

    return len(linhas)


def intervalo_necessario(cursor_origem) -> tuple[date, date]:
    """Le no OLTP a menor e a maior data referenciada pelos fatos."""
    cursor_origem.execute(
        """
        SELECT MIN(dt), MAX(dt) FROM (
            SELECT MIN(OrderDate) AS dt FROM Sales.SalesOrderHeader
            UNION ALL SELECT MAX(OrderDate) FROM Sales.SalesOrderHeader
            UNION ALL SELECT MAX(DueDate)   FROM Sales.SalesOrderHeader
            UNION ALL SELECT MAX(ShipDate)  FROM Sales.SalesOrderHeader
            UNION ALL SELECT MIN(OrderDate) FROM Purchasing.PurchaseOrderHeader
            UNION ALL SELECT MAX(OrderDate) FROM Purchasing.PurchaseOrderHeader
            UNION ALL SELECT MAX(ShipDate)  FROM Purchasing.PurchaseOrderHeader
            UNION ALL SELECT MAX(DueDate)   FROM Purchasing.PurchaseOrderDetail
        ) AS datas
        WHERE dt IS NOT NULL;
        """
    )
    minimo, maximo = cursor_origem.fetchone()
    return minimo.date(), maximo.date()
