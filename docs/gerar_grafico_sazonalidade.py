"""Gera docs/imagens/sazonalidade_canal.png a partir de kpi.mv_sazonalidade.

    python docs/gerar_grafico_sazonalidade.py

Requer ``matplotlib``, ``psycopg`` e o conteiner dw-postgres em execucao.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import psycopg

SAIDA = Path(__file__).resolve().parent / "imagens" / "sazonalidade_canal.png"
CONEXAO = "host=localhost port=5434 dbname=dw_adventureworks user=dw_user password=dw_pass"

CONSULTA = """
SELECT nr_mes,
       MAX(nr_indice_sazonal) FILTER (WHERE nm_canal = 'Internet'),
       MAX(nr_indice_sazonal) FILTER (WHERE nm_canal = 'Revenda')
  FROM kpi.mv_sazonalidade
 GROUP BY nr_mes
 ORDER BY nr_mes;
"""

MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
COR_INTERNET = "#2a78d6"
COR_REVENDA = "#eb6834"
TEXTO = "#0b0b0b"
TEXTO_SECUNDARIO = "#52514e"
GRADE = "#e4e3df"


def serie(eixo, meses, valores, cor, marcador, rotulo) -> None:
    eixo.plot(meses, valores, color=cor, linewidth=1.6, marker=marcador,
              markersize=4.5, markeredgecolor="white", markeredgewidth=0.6,
              label=rotulo, zorder=3)


def main() -> None:
    with psycopg.connect(CONEXAO) as conexao:
        linhas = conexao.execute(CONSULTA).fetchall()
    meses = [linha[0] for linha in linhas]
    internet = [float(linha[1]) for linha in linhas]
    revenda = [float(linha[2]) for linha in linhas]

    plt.rcParams["font.family"] = "Arial"
    figura, eixo = plt.subplots(figsize=(6.3, 2.55), dpi=320)

    eixo.axhline(100, color=TEXTO_SECUNDARIO, linewidth=0.8, linestyle=(0, (4, 3)), zorder=2)
    eixo.text(12.45, 100, "média\ndo ano", fontsize=6.8, va="center", color=TEXTO_SECUNDARIO)
    serie(eixo, meses, internet, COR_INTERNET, "o", "Internet")
    serie(eixo, meses, revenda, COR_REVENDA, "s", "Revenda")

    pico_internet = max(range(12), key=internet.__getitem__)
    pico_revenda = max(range(12), key=revenda.__getitem__)
    eixo.annotate(f"Internet em {MESES[pico_internet]}: {internet[pico_internet]:.0f}".replace(".", ","),
                  (meses[pico_internet], internet[pico_internet]), xytext=(-8, 3),
                  textcoords="offset points", ha="right", fontsize=7.5, color=TEXTO)
    eixo.annotate(f"Revenda em {MESES[pico_revenda]}: {revenda[pico_revenda]:.0f}".replace(".", ","),
                  (meses[pico_revenda], revenda[pico_revenda]), xytext=(0, 6),
                  textcoords="offset points", ha="center", fontsize=7.5, color=TEXTO)

    eixo.set_xticks(meses, MESES, fontsize=7.5, color=TEXTO_SECUNDARIO)
    eixo.set_xlim(0.6, 12.4)
    eixo.set_ylim(40, 175)
    eixo.set_yticks([50, 100, 150])
    eixo.tick_params(axis="y", labelsize=7.5, colors=TEXTO_SECUNDARIO, length=0)
    eixo.tick_params(axis="x", length=0)
    eixo.set_ylabel("Índice sazonal", fontsize=7.5, color=TEXTO_SECUNDARIO)
    eixo.grid(axis="y", color=GRADE, linewidth=0.5, zorder=0)
    for lado in ("top", "right", "left"):
        eixo.spines[lado].set_visible(False)
    eixo.spines["bottom"].set_color(GRADE)
    eixo.legend(loc="upper left", ncols=2, fontsize=7.5, frameon=False,
                handlelength=1.8, borderaxespad=0.1)

    figura.tight_layout(pad=0.4)
    figura.subplots_adjust(right=0.93)
    figura.savefig(SAIDA, facecolor="white")
    plt.close(figura)
    print(f"Grafico salvo em {SAIDA}")


if __name__ == "__main__":
    main()
