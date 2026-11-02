"""Compoe docs/imagens/dags_auxiliares.png com as telas das DAGs de apoio.

    python docs/gerar_figuras_dag.py

A DAG de indicadores e alta e a de simulacao e estreita. Lado a lado, as duas
cabem na largura do artigo sem perder a legibilidade. Requer ``pillow``.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

DIR_IMAGENS = Path(__file__).resolve().parent / "imagens"
SAIDA = DIR_IMAGENS / "dags_auxiliares.png"

LARGURA, ALTURA = 3200, 1750
MARGEM = 30
ALTURA_ROTULO = 90
COR_TEXTO = "#1a1a1a"


def main() -> None:
    fonte = ImageFont.truetype("arial.ttf", 56)
    tela = Image.new("RGB", (LARGURA, ALTURA), "white")
    desenho = ImageDraw.Draw(tela)

    kpi = Image.open(DIR_IMAGENS / "kpi_grafo.png").convert("RGB")
    altura_kpi = ALTURA - ALTURA_ROTULO - 2 * MARGEM
    largura_kpi = round(kpi.width * altura_kpi / kpi.height)
    desenho.text((MARGEM, MARGEM), "kpi_adventureworks", font=fonte, fill=COR_TEXTO)
    tela.paste(kpi.resize((largura_kpi, altura_kpi), Image.LANCZOS), (MARGEM, MARGEM + ALTURA_ROTULO))

    simulacao = Image.open(DIR_IMAGENS / "simulacao_grafo.png").convert("RGB")
    x_sim = largura_kpi + 3 * MARGEM
    largura_sim = LARGURA - x_sim - MARGEM
    altura_sim = round(simulacao.height * largura_sim / simulacao.width)
    y_sim = (ALTURA - altura_sim) // 2
    desenho.text((x_sim, y_sim - ALTURA_ROTULO), "simular_movimento_oltp", font=fonte, fill=COR_TEXTO)
    tela.paste(simulacao.resize((largura_sim, altura_sim), Image.LANCZOS), (x_sim, y_sim))

    tela.save(SAIDA)
    print(f"Figura salva em {SAIDA}")


if __name__ == "__main__":
    main()
