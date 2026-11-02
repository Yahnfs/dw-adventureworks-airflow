"""Gera docs/modelo_estrela.png, o diagrama do modelo multidimensional.

    python docs/gerar_diagrama.py

As fatos ficam ao centro e cada dimensao se liga a elas por uma reta. As
dimensoes conformadas ocupam a coluna entre as duas fatos, pois sao as mesmas
tabelas fisicas nas duas estrelas. Nenhuma dimensao se liga a outra.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Patch

SAIDA = Path(__file__).resolve().parent / "modelo_estrela.png"

COR_FATO = ("#1F3864", "#FFFFFF")
COR_CONFORMADA = ("#FBE5D6", "#1A1A1A")
COR_EXCLUSIVA = ("#E2EFDA", "#1A1A1A")
COR_BORDA = "#404040"
COR_LIGACAO = "#595959"

LARGURA = 100.0
ALTURA = 74.0
TOPO = 73.5
BASE = 0.5

L_DIM = 16.5
L_FATO = 17.5
X_ESQ = 0.5
X_VENDAS = 20.5
X_CENTRO = 41.5
X_COMPRAS = 61.5
X_DIR = 82.5
L_DIR = 17.0

ALT_LINHA = 2.2
ALT_CABECALHO = 4.0

Tabela = tuple[str, list[str]]


def altura_tabela(linhas: list[str]) -> float:
    return ALT_CABECALHO + ALT_LINHA * len(linhas)


def caixa(eixo, x, topo, largura, titulo, linhas, cores, altura=None) -> float:
    """Desenha uma tabela com o topo em ``topo``. Devolve o centro vertical.

    Linhas iniciadas por ``#`` sao rotulos de secao, em negrito.
    """
    fundo, texto = cores
    altura = altura or altura_tabela(linhas)
    eixo.add_patch(
        FancyBboxPatch(
            (x, topo - altura), largura, altura,
            boxstyle="round,pad=0,rounding_size=0.7",
            facecolor=fundo, edgecolor=COR_BORDA, linewidth=0.6, zorder=3,
        )
    )
    eixo.text(x + largura / 2, topo - 1.6, titulo, ha="center", va="center",
              fontsize=6.8, fontweight="bold", color=texto, zorder=4)
    eixo.plot([x + 0.8, x + largura - 0.8], [topo - 3.0] * 2,
              color=texto, linewidth=0.35, alpha=0.6, zorder=4)
    for indice, linha in enumerate(linhas):
        secao = linha.startswith("#")
        eixo.text(x + 1.0, topo - 4.3 - indice * ALT_LINHA, linha.lstrip("#"),
                  ha="left", va="center", fontsize=5.7,
                  fontweight="bold" if secao else "normal", color=texto, zorder=4)
    return topo - altura / 2


def ligar(eixo, x1, x2, y, esquerda, direita) -> None:
    """Liga dimensao e fato por uma reta, com a cardinalidade nas pontas."""
    eixo.plot([x1, x2], [y, y], color=COR_LIGACAO, linewidth=0.7, zorder=1)
    eixo.text(x1 + 0.4, y + 0.7, esquerda, fontsize=5.2, ha="left", color=COR_LIGACAO)
    eixo.text(x2 - 0.4, y + 0.7, direita, fontsize=5.2, ha="right", color=COR_LIGACAO)


def coluna(eixo, x, largura, tabelas: list[Tabela], cores) -> list[float]:
    """Distribui as tabelas na altura util. Devolve o centro de cada uma."""
    ocupado = sum(altura_tabela(linhas) for _, linhas in tabelas)
    folga = (TOPO - BASE - ocupado) / (len(tabelas) - 1)
    centros = []
    topo = TOPO
    for titulo, linhas in tabelas:
        centros.append(caixa(eixo, x, topo, largura, titulo, linhas, cores))
        topo -= altura_tabela(linhas) + folga
    return centros


def main() -> None:
    plt.rcParams["font.family"] = "Arial"
    figura, eixo = plt.subplots(figsize=(7.1, 5.25), dpi=320)
    eixo.set_xlim(0, LARGURA)
    eixo.set_ylim(0, ALTURA)
    eixo.axis("off")

    exclusivas: list[Tabela] = [
        ("dim_cliente", ["PK sk_cliente", "id_cliente, cd_conta", "tp_cliente", "nm_cliente, ds_email"]),
        ("dim_territorio", ["PK sk_territorio", "id_territorio", "nm_territorio", "nm_grupo, nm_pais"]),
        ("dim_geografia", ["PK sk_geografia", "id_endereco", "ds_cidade, nm_estado", "nm_pais, nm_regiao"]),
        ("dim_promocao", ["PK sk_promocao", "id_promocao", "ds_promocao, tp_promocao", "pc_desconto"]),
        ("dim_canal_venda", ["PK sk_canal", "cd_canal, nm_canal"]),
    ]
    for y in coluna(eixo, X_ESQ, L_DIM, exclusivas, COR_EXCLUSIVA):
        ligar(eixo, X_ESQ + L_DIM, X_VENDAS, y, "1", "N")

    conformadas: list[Tabela] = [
        ("dim_tempo", ["PK sk_tempo (AAAAMMDD)", "dt_data, nr_ano", "nr_trimestre, nr_mes", "nm_mes, fl_fim_semana"]),
        ("dim_produto (SCD 2)", ["PK sk_produto", "id_produto, nm_produto", "nm_categoria, nm_modelo", "vl_preco_lista",
                                 "vl_custo_padrao, nr_versao", "dt_inicio_validade", "dt_fim_validade, fl_corrente"]),
        ("dim_funcionario", ["PK sk_funcionario", "id_funcionario", "nm_funcionario, ds_cargo"]),
        ("dim_metodo_envio", ["PK sk_metodo_envio", "id_metodo_envio", "nm_metodo_envio"]),
        ("dim_status_pedido", ["PK sk_status", "ds_dominio, nm_status", "fl_concluido, fl_cancelado"]),
    ]
    for y in coluna(eixo, X_CENTRO, L_DIM, conformadas, COR_CONFORMADA):
        ligar(eixo, X_VENDAS + L_FATO, X_CENTRO, y, "N", "1")
        ligar(eixo, X_CENTRO + L_DIM, X_COMPRAS, y, "1", "N")

    caixa(
        eixo, X_VENDAS, TOPO, L_FATO, "fato_vendas",
        [
            "#Grão: item de pedido", "",
            "#Chaves estrangeiras (12)",
            "sk_tempo_pedido", "sk_tempo_vencimento", "sk_tempo_envio",
            "sk_produto", "sk_cliente", "sk_vendedor", "sk_territorio",
            "sk_promocao", "sk_geografia_entrega", "sk_metodo_envio",
            "sk_canal", "sk_status", "",
            "#Dimensões degeneradas",
            "id_item_venda, id_pedido", "nr_pedido", "",
            "#Medidas",
            "qt_vendida, vl_bruto", "vl_desconto, vl_liquido", "vl_custo_total",
            "vl_margem_bruta", "vl_frete_rateado", "vl_imposto_rateado",
            "qt_dias_entrega",
        ],
        COR_FATO, altura=TOPO - BASE,
    )
    caixa(
        eixo, X_COMPRAS, TOPO, L_FATO, "fato_compras",
        [
            "#Grão: item de ordem", "#de compra", "",
            "#Chaves estrangeiras (8)",
            "sk_tempo_pedido", "sk_tempo_previsto", "sk_tempo_recebimento",
            "sk_produto", "sk_fornecedor", "sk_comprador",
            "sk_metodo_envio", "sk_status", "",
            "#Dimensões degeneradas",
            "id_item_compra", "id_ordem_compra", "",
            "#Medidas",
            "qt_pedida, qt_recebida", "qt_rejeitada, qt_aceita",
            "vl_preco_unitario", "vl_total_linha", "vl_frete_rateado",
            "vl_imposto_rateado", "qt_dias_recebimento",
        ],
        COR_FATO, altura=TOPO - BASE,
    )

    fornecedor = ["PK sk_fornecedor", "id_fornecedor", "nm_fornecedor", "ds_nivel_credito", "fl_preferencial"]
    y = caixa(eixo, X_DIR, 46.0, L_DIR, "dim_fornecedor", fornecedor, COR_EXCLUSIVA)
    ligar(eixo, X_COMPRAS + L_FATO, X_DIR, y, "N", "1")

    legenda = [
        Patch(facecolor=COR_FATO[0], edgecolor=COR_BORDA, label="Tabela fato"),
        Patch(facecolor=COR_CONFORMADA[0], edgecolor=COR_BORDA, label="Dimensão conformada"),
        Patch(facecolor=COR_EXCLUSIVA[0], edgecolor=COR_BORDA, label="Dimensão de uma só fato"),
    ]
    eixo.legend(handles=legenda, loc="upper left", bbox_to_anchor=(0.825, 1.0),
                fontsize=5.6, frameon=False, handlelength=1.2, borderaxespad=0.1)

    papeis = [
        "Papéis:",
        "dim_tempo: pedido, prazo e",
        "envio ou recebimento",
        "dim_funcionario: vendedor",
        "ou comprador",
    ]
    for indice, linha in enumerate(papeis):
        eixo.text(X_DIR + 0.5, 22.0 - indice * ALT_LINHA, linha, fontsize=5.6,
                  fontweight="bold" if indice == 0 else "normal", color="#1A1A1A")

    figura.subplots_adjust(left=0.005, right=0.995, top=0.995, bottom=0.005)
    figura.savefig(SAIDA, facecolor="white")
    plt.close(figura)
    print(f"Diagrama salvo em {SAIDA}")


if __name__ == "__main__":
    main()
