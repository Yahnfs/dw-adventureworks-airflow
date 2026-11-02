"""Gera o artigo academico em .docx conforme o Guia Unisales (6. ed., 2024).

    python docs/artigo/gerar_artigo.py

Regras de formatacao aplicadas, com o item do Guia entre parenteses:

* A4; margens superior e esquerda 3 cm, inferior e direita 2 cm (1.2.1, 1.2.2)
* Arial 12, entrelinha 1,0 em todo o texto (1.2.3)
* Fonte 10 em legendas e fontes de ilustracoes e paginacao (1.2.3)
* Paragrafos sem recuo de primeira linha, 0 pt antes e 6 pt depois (1.2.4)
* Titulos "1 MAIUSCULAS NEGRITO" e "1.1 MAIUSCULAS NORMAL" (1.2.5)
* Paginacao em Arial 10 (1.2.6)
* Ilustracoes centralizadas e com borda; titulo acima e fonte abaixo (1.2.10)
* Quadros fechados (1.2.12)
* Referencias em ordem alfabetica, entrelinha simples, separadas por um
  paragrafo em branco (3.1)

A estrutura de secoes segue o enunciado da atividade: Introducao,
Desenvolvimento (Data ETL, Modelo de dados, Indicadores, Resultados dos
indicadores) e Consideracoes Finais.
"""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

DIR_ARTIGO = Path(__file__).resolve().parent
DIR_DOCS = DIR_ARTIGO.parent
DIR_IMAGENS = DIR_DOCS / "imagens"
SAIDA = DIR_ARTIGO / "Artigo_DW_AdventureWorks_Airflow_Unisales.docx"

FONTE = "Arial"
FONTE_CODIGO = "Consolas"
FONTE_PROPRIA = "Fonte: elaboração própria (2026)."
REPOSITORIO = "https://github.com/Yahnfs/dw-adventureworks-airflow"

_contadores = {"quadro": 0, "figura": 0}


def _proximo(tipo: str) -> int:
    _contadores[tipo] += 1
    return _contadores[tipo]


# ---------------------------------------------------------------------------
# Formatacao base
# ---------------------------------------------------------------------------

def configurar_documento() -> Document:
    documento = Document()

    secao_doc = documento.sections[0]
    secao_doc.page_width, secao_doc.page_height = Cm(21.0), Cm(29.7)
    secao_doc.top_margin, secao_doc.left_margin = Cm(3.0), Cm(3.0)
    secao_doc.bottom_margin, secao_doc.right_margin = Cm(2.0), Cm(2.0)

    estilo = documento.styles["Normal"]
    estilo.font.name = FONTE
    estilo.font.size = Pt(12)
    estilo.element.rPr.rFonts.set(qn("w:eastAsia"), FONTE)
    formato = estilo.paragraph_format
    formato.line_spacing_rule = WD_LINE_SPACING.SINGLE
    formato.space_before = Pt(0)
    formato.space_after = Pt(6)

    _numerar_paginas(secao_doc)
    return documento


def _numerar_paginas(secao_doc) -> None:
    """Numero da pagina no cabecalho, a direita, em Arial 10 (Guia 1.2.6)."""
    paragrafo = secao_doc.header.paragraphs[0]
    paragrafo.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    paragrafo.paragraph_format.space_after = Pt(0)
    execucao = paragrafo.add_run()
    _fonte(execucao, 10)

    inicio = OxmlElement("w:fldChar")
    inicio.set(qn("w:fldCharType"), "begin")
    instrucao = OxmlElement("w:instrText")
    instrucao.set(qn("xml:space"), "preserve")
    instrucao.text = "PAGE"
    fim = OxmlElement("w:fldChar")
    fim.set(qn("w:fldCharType"), "end")
    for elemento in (inicio, instrucao, fim):
        execucao._r.append(elemento)


def _fonte(execucao, tamanho=12, negrito=False, italico=False, nome=FONTE):
    execucao.font.name = nome
    execucao.font.size = Pt(tamanho)
    execucao.bold = negrito
    execucao.italic = italico
    execucao._element.rPr.rFonts.set(qn("w:eastAsia"), nome)
    return execucao


def _sombrear(celula, cor_hex: str) -> None:
    elemento = OxmlElement("w:shd")
    elemento.set(qn("w:val"), "clear")
    elemento.set(qn("w:fill"), cor_hex)
    celula._tc.get_or_add_tcPr().append(elemento)


def vazio(doc: Document, tamanho: int = 12) -> None:
    """Paragrafo em branco: o 'enter' previsto pelo Guia entre elementos."""
    paragrafo = doc.add_paragraph()
    paragrafo.paragraph_format.space_after = Pt(0)
    _fonte(paragrafo.add_run(""), tamanho)


# ---------------------------------------------------------------------------
# Elementos pre-textuais
# ---------------------------------------------------------------------------

def titulo_trabalho(doc: Document, texto: str, subtitulo: str) -> None:
    paragrafo = doc.add_paragraph()
    paragrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragrafo.paragraph_format.space_after = Pt(0)
    _fonte(paragrafo.add_run(texto.upper()), 12, negrito=True)

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.paragraph_format.space_after = Pt(12)
    _fonte(sub.add_run(subtitulo), 12, negrito=True)


def autoria(doc: Document, linhas: list[str]) -> None:
    for texto in linhas:
        paragrafo = doc.add_paragraph()
        paragrafo.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        paragrafo.paragraph_format.space_after = Pt(0)
        _fonte(paragrafo.add_run(texto), 12)
    vazio(doc)


def bloco_resumo(doc: Document, rotulo: str, texto: str,
                 rotulo_chaves: str, chaves: str) -> None:
    corpo = doc.add_paragraph()
    corpo.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    corpo.paragraph_format.space_after = Pt(6)
    _fonte(corpo.add_run(f"{rotulo}: "), 12, negrito=True)
    _fonte(corpo.add_run(texto), 12)

    palavras = doc.add_paragraph()
    palavras.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    palavras.paragraph_format.space_after = Pt(12)
    _fonte(palavras.add_run(f"{rotulo_chaves}: "), 12, negrito=True)
    _fonte(palavras.add_run(chaves), 12)


# ---------------------------------------------------------------------------
# Titulos de secao (Guia 1.2.5)
# ---------------------------------------------------------------------------

def _titulo(doc: Document, texto: str, negrito: bool, maiusculas: bool):
    paragrafo = doc.add_paragraph()
    paragrafo.alignment = WD_ALIGN_PARAGRAPH.LEFT
    paragrafo.paragraph_format.space_before = Pt(0)
    paragrafo.paragraph_format.space_after = Pt(0)
    paragrafo.paragraph_format.keep_with_next = True
    _fonte(paragrafo.add_run(texto.upper() if maiusculas else texto),
           12, negrito=negrito)
    return paragrafo


def secao(doc: Document, numero: str, texto: str) -> None:
    """Secao primaria: tamanho 12, negrito, maiusculas."""
    vazio(doc)
    _titulo(doc, f"{numero} {texto}".strip(), negrito=True, maiusculas=True)


def subsecao(doc: Document, numero: str, texto: str) -> None:
    """Secao secundaria: tamanho 12, normal, maiusculas."""
    vazio(doc)
    _titulo(doc, f"{numero} {texto}", negrito=False, maiusculas=True)


# ---------------------------------------------------------------------------
# Corpo do texto
# ---------------------------------------------------------------------------

def par(doc: Document, texto: str):
    paragrafo = doc.add_paragraph()
    paragrafo.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    paragrafo.paragraph_format.space_after = Pt(6)
    _fonte(paragrafo.add_run(texto), 12)
    return paragrafo


# ---------------------------------------------------------------------------
# Ilustracoes e quadros (Guia 1.2.10 e 1.2.12)
# ---------------------------------------------------------------------------

def legenda_superior(doc: Document, texto: str) -> None:
    paragrafo = doc.add_paragraph()
    paragrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragrafo.paragraph_format.space_before = Pt(0)
    paragrafo.paragraph_format.space_after = Pt(0)
    paragrafo.paragraph_format.keep_with_next = True
    _fonte(paragrafo.add_run(texto), 10)


def legenda_fonte(doc: Document, texto: str) -> None:
    paragrafo = doc.add_paragraph()
    paragrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragrafo.paragraph_format.space_before = Pt(0)
    paragrafo.paragraph_format.space_after = Pt(6)
    _fonte(paragrafo.add_run(texto), 10)


def _manter_na_pagina(tabela) -> None:
    """Impede que um quadro se divida entre paginas e o prende a sua fonte."""
    for linha in tabela.rows:
        propriedades = linha._tr.get_or_add_trPr()
        propriedades.append(OxmlElement("w:cantSplit"))
        for celula in linha.cells:
            for paragrafo in celula.paragraphs:
                paragrafo.paragraph_format.keep_with_next = True


def figura(doc: Document, caminhos: list[Path], titulo: str, fonte: str,
           largura_cm: float = 15.0) -> None:
    numero = _proximo("figura")
    legenda_superior(doc, f"Figura {numero} – {titulo}")

    tabela = doc.add_table(rows=1, cols=1)
    tabela.style = "Table Grid"
    tabela.alignment = WD_TABLE_ALIGNMENT.CENTER
    celula = tabela.rows[0].cells[0]
    celula.text = ""
    for indice, caminho in enumerate(caminhos):
        paragrafo = celula.paragraphs[0] if indice == 0 else celula.add_paragraph()
        paragrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragrafo.paragraph_format.space_after = Pt(0)
        paragrafo.paragraph_format.keep_with_next = True
        paragrafo.add_run().add_picture(str(caminho), width=Cm(largura_cm))

    legenda_fonte(doc, fonte)


def _margens_celulas(tabela, cm: float = 0.04) -> None:
    """Reduz o espacamento interno das celulas, adensando quadros extensos."""
    largura = str(int(cm * 567))  # centimetros -> twips
    propriedades = tabela._tbl.tblPr
    margens = OxmlElement("w:tblCellMar")
    for lado in ("top", "left", "bottom", "right"):
        elemento = OxmlElement(f"w:{lado}")
        elemento.set(qn("w:w"), largura)
        elemento.set(qn("w:type"), "dxa")
        margens.append(elemento)
    propriedades.append(margens)


def quadro(doc: Document, titulo: str, cabecalho: list[str],
           linhas: list[list[str]], fonte: str, tamanho: float = 9,
           larguras: list[float] | None = None) -> None:
    legenda_superior(doc, f"Quadro {_proximo('quadro')} – {titulo}")

    tabela = doc.add_table(rows=1, cols=len(cabecalho))
    tabela.style = "Table Grid"
    tabela.alignment = WD_TABLE_ALIGNMENT.CENTER

    for indice, texto in enumerate(cabecalho):
        celula = tabela.rows[0].cells[indice]
        celula.text = ""
        paragrafo = celula.paragraphs[0]
        paragrafo.paragraph_format.space_after = Pt(0)
        _fonte(paragrafo.add_run(texto), tamanho, negrito=True)
        _sombrear(celula, "D9D9D9")

    for valores in linhas:
        celulas = tabela.add_row().cells
        for indice, texto in enumerate(valores):
            celula = celulas[indice]
            celula.text = ""
            paragrafo = celula.paragraphs[0]
            paragrafo.paragraph_format.space_after = Pt(0)
            _fonte(paragrafo.add_run(texto), tamanho)

    _margens_celulas(tabela)

    if larguras:
        for linha in tabela.rows:
            for indice, largura in enumerate(larguras):
                linha.cells[indice].width = Cm(largura)

    _manter_na_pagina(tabela)
    legenda_fonte(doc, fonte)


def quadro_codigo(doc: Document, titulo: str, linhas: list[str],
                  fonte: str = FONTE_PROPRIA, tamanho: float = 8) -> None:
    """Trecho de codigo emoldurado, apresentado como quadro (Guia 1.2.12)."""
    legenda_superior(doc, f"Quadro {_proximo('quadro')} – {titulo}")

    tabela = doc.add_table(rows=1, cols=1)
    tabela.style = "Table Grid"
    tabela.alignment = WD_TABLE_ALIGNMENT.CENTER
    _margens_celulas(tabela)
    celula = tabela.rows[0].cells[0]
    _sombrear(celula, "F2F2F2")
    celula.text = ""

    for indice, linha in enumerate(linhas):
        paragrafo = celula.paragraphs[0] if indice == 0 else celula.add_paragraph()
        paragrafo.alignment = WD_ALIGN_PARAGRAPH.LEFT
        paragrafo.paragraph_format.space_before = Pt(0)
        paragrafo.paragraph_format.space_after = Pt(0)
        _fonte(paragrafo.add_run(linha if linha.strip() else " "),
               tamanho, nome=FONTE_CODIGO)

    _manter_na_pagina(tabela)
    legenda_fonte(doc, fonte)


def referencia(doc: Document, partes: list[tuple[str, bool]]) -> None:
    paragrafo = doc.add_paragraph()
    paragrafo.alignment = WD_ALIGN_PARAGRAPH.LEFT
    paragrafo.paragraph_format.space_before = Pt(0)
    paragrafo.paragraph_format.space_after = Pt(6)
    for texto, negrito in partes:
        _fonte(paragrafo.add_run(texto), 12, negrito=negrito)


# ---------------------------------------------------------------------------
# Conteudo do artigo
# ---------------------------------------------------------------------------

def pre_textuais(doc: Document) -> None:
    titulo_trabalho(
        doc,
        "Orquestração de um Data Warehouse com Apache Airflow",
        "ETL incremental e modelagem Star Schema sobre a base AdventureWorks",
    )
    autoria(doc, ["Yahn de Freitas Santos*", "James Alves**"])

    bloco_resumo(
        doc, "RESUMO",
        "Este artigo apresenta o projeto e a implementação individual de um "
        "Data Warehouse construído a partir da base transacional "
        "AdventureWorks, com modelagem Star Schema em PostgreSQL e processos "
        "de ETL orquestrados pelo Apache Airflow. O modelo reúne duas tabelas "
        "fato e onze dimensões, cinco delas conformadas, e sustenta dez "
        "indicadores calculados em SQL. A carga incremental combina marcas "
        "d'água sobre todas as tabelas de origem de cada entidade, escrita "
        "idempotente e Slowly Changing Dimensions. A carga inicial processou "
        "170.525 registros; um ciclo sem alterações extraiu zero linhas e um "
        "ciclo com cinco eventos simulados extraiu exatamente as 17 linhas "
        "afetadas. Os indicadores revelaram que a Revenda gera 73,27% da "
        "receita e apenas 3,80% da margem bruta, além de padrões sazonais "
        "opostos entre os canais de venda.",
        "Palavras-chave",
        "Data Warehouse. Star Schema. ETL incremental. Apache Airflow. "
        "Indicadores.",
    )
    bloco_resumo(
        doc, "ABSTRACT",
        "This article presents the individual design and implementation of a "
        "Data Warehouse built from the AdventureWorks transactional database, "
        "using Star Schema modeling on PostgreSQL and ETL processes "
        "orchestrated by Apache Airflow. The model comprises two fact tables "
        "and eleven dimensions, five of them conformed, and supports ten "
        "indicators computed in SQL. The incremental load combines high-water "
        "marks over every source table of each entity, idempotent writes and "
        "Slowly Changing Dimensions. The initial load processed 170,525 "
        "records; a cycle with no changes extracted zero rows, and a cycle "
        "with five simulated events extracted exactly the 17 affected rows. "
        "The indicators showed that the reseller channel generates 73.27% of "
        "revenue but only 3.80% of gross margin, along with opposite seasonal "
        "patterns between sales channels.",
        "Keywords",
        "Data Warehouse. Star Schema. Incremental ETL. Apache Airflow. "
        "Indicators.",
    )


def introducao(doc: Document) -> None:
    secao(doc, "1", "Introdução")
    par(doc,
        "Sistemas transacionais (OLTP) são normalizados para registrar "
        "operações com integridade, o que fragmenta a informação em dezenas "
        "de tabelas e dificulta a análise gerencial (Chaudhuri; Dayal, 1997). "
        "O Data Warehouse responde a esse impasse com um repositório "
        "analítico separado da operação, orientado por assunto, integrado, "
        "não volátil e variável no tempo (Inmon, 2005), organizado em modelos "
        "multidimensionais que privilegiam a leitura (Kimball; Ross, 2013).")
    par(doc,
        "Manter esse repositório exige mais do que um script de carga. A "
        "rotina precisa executar sem intervenção, processar somente o que "
        "mudou, recuperar-se de falhas e registrar o que fez. Esse é o papel "
        "de um orquestrador como o Apache Airflow, que descreve o pipeline "
        "como um grafo acíclico dirigido (DAG) de tarefas e dependências "
        "(Apache Software Foundation, 2026).")
    par(doc,
        "O objetivo deste trabalho é projetar e implementar individualmente "
        "um Data Warehouse sobre a base AdventureWorks, com modelo Star "
        "Schema em PostgreSQL, ETL incremental orquestrada pelo Airflow e dez "
        "indicadores calculados em SQL. O trabalho reutiliza o contexto do "
        "Produto 1, desenvolvido em dupla (Santos, 2026a), que entregou o "
        "modelo dimensional e uma ETL em Python executada manualmente. As "
        "contribuições individuais são a orquestração, a revisão da detecção "
        "de mudanças, a conferência automática entre origem e destino e a "
        "reformulação dos indicadores. O código-fonte, os scripts e a "
        f"documentação técnica estão em repositório público: {REPOSITORIO} "
        "(Santos, 2026b).")


def data_etl(doc: Document) -> None:
    subsecao(doc, "2.1", "Data ETL")
    par(doc,
        "A origem é a base AdventureWorks2022, em SQL Server, que simula uma "
        "fabricante e distribuidora de bicicletas (Microsoft, 2024). Suas 71 "
        "tabelas concentram-se nos esquemas Sales, Purchasing, Production, "
        "Person e HumanResources. A análise desse modelo orientou três "
        "decisões. Quase todas as tabelas mantêm a coluna de auditoria "
        "ModifiedDate, o que viabiliza a captura de mudanças sem gatilhos nem "
        "leitura de log. Pedidos separam cabeçalho e itens, o que define o "
        "grão candidato das fatos. E as entidades de negócio estão espalhadas: "
        "o nome do cliente reside em Person.Person e a cota do vendedor, em "
        "Sales.SalesPerson, fora da tabela principal de cada entidade.")
    par(doc,
        "Todo o ambiente é descrito em Docker Compose: Apache Airflow 3.3.2, "
        "SQL Server 2022 restaurado do backup oficial e PostgreSQL 16 para o "
        "Data Warehouse. Uma única subida restaura a origem, cria o banco e "
        "dispara a primeira carga, o que torna o trabalho reproduzível.")
    par(doc,
        "A estratégia incremental é a marca d'água (high-water mark): a "
        "tabela meta.etl_controle guarda a maior data de modificação já "
        "processada por entidade, e a extração seguinte lê apenas o que a "
        "supera (Kimball; Caserta, 2004; Vaisman; Zimányi, 2022). Na primeira "
        "execução a marca vale 1900-01-01, de modo que a carga completa não "
        "exige código próprio. Três ajustes corrigem falhas do Produto 1. "
        "Primeiro, a marca passa a considerar todas as tabelas que alimentam "
        "a entidade, e não só a principal, como mostra o Quadro 1. Sem isso, "
        "a troca do nome de um cliente passaria despercebida. Segundo, o "
        "parâmetro é convertido para datetime, pois o driver o envia como "
        "datetime2 e o SQL Server compara a coluna pela fração exata, o que "
        "faria a linha que definiu a marca voltar em todo ciclo. Terceiro, "
        "foi removida a janela de retrocesso, que reextraía 20.023 linhas por "
        "ciclo porque 19.820 clientes compartilham a mesma data de "
        "modificação; o risco que ela cobria passou à validação final.")
    quadro_codigo(doc, "Extração incremental e marca d'água da dimensão cliente", [
        "SELECT q.* FROM (<consulta-base da entidade>) AS q",
        " WHERE q.dt_modificacao_origem > CAST(? AS datetime)",
        " ORDER BY q.dt_modificacao_origem, q.<chave>;",
        "",
        "-- coluna calculada na consulta-base de dim_cliente:",
        "(SELECT MAX(m) FROM (VALUES (c.ModifiedDate), (pe.ModifiedDate),",
        "                            (st.ModifiedDate), (ea.ModifiedDate)) AS x(m))",
        "    AS dt_modificacao_origem",
    ])
    par(doc,
        "No destino, a escrita é idempotente: as fatos usam INSERT ... ON "
        "CONFLICT sobre a chave da transação de origem, e as dimensões de "
        "tipo 1 só são regravadas quando um resumo MD5 dos atributos diverge. "
        "A dimensão produto, de tipo 2, encerra a versão vigente e insere a "
        "nova dentro da mesma transação. A marca d'água avança nessa mesma "
        "transação, portanto uma falha nunca deixa janela perdida: o ciclo "
        "seguinte reprocessa o que ficou pendente.")
    par(doc,
        "A DAG etl_adventureworks_incremental (Figura 1) tem 26 tarefas e "
        "executa diariamente às 2h, sem sobreposição de execuções e com duas "
        "retentativas por tarefa. A faixa superior mostra o fluxo geral; a "
        "inferior expande os grupos em uma execução real, na qual somente as "
        "entidades com movimento executaram (verde), enquanto as demais foram "
        "ignoradas (rosa). O Quadro 2 explica cada tarefa e suas dependências.")
    figura(
        doc,
        [DIR_IMAGENS / "ciclo3_recolhido.png", DIR_IMAGENS / "ciclo3_grafo.png"],
        "DAG de ETL no Airflow: fluxo geral e grupos expandidos (ciclo 3)",
        "Fonte: captura da interface do Apache Airflow (2026).",
    )
    par(doc,
        "As dependências refletem o modelo. O calendário e as dimensões "
        "precedem as fatos porque a resolução das chaves substitutas depende "
        "deles; as oito dimensões executam em paralelo porque não dependem "
        "umas das outras. Separar extrair e transformar permite repetir uma "
        "transformação sem voltar à origem, já que o staging está confirmado. "
        "A regra none_failed mantém a carga das fatos mesmo quando todas as "
        "dimensões terminam ignoradas.")
    quadro(
        doc, "Tarefas da DAG de ETL e suas dependências",
        ["Tarefa", "Função", "Depende de"],
        [
            ["verificar_ambiente", "Testa origem e destino; 10 retentativas cobrem a restauração inicial", "Início"],
            ["preparar_lote", "Zera as marcas se o parâmetro recarga_completa for verdadeiro", "verificar_ambiente"],
            ["carregar_dim_tempo", "Gera o calendário, em anos inteiros, a partir das datas da origem", "preparar_lote"],
            ["dimensoes.<ent>.extrair", "Copia o recorte incremental para stg; sem linhas, termina como skipped", "carregar_dim_tempo"],
            ["dimensoes.<ent>.transformar", "Promove stg para dw e avança a marca, na mesma transação", "extrair da entidade"],
            ["fatos.<ent>.extrair", "Igual às dimensões, com regra none_failed", "Grupo dimensoes"],
            ["fatos.<ent>.transformar", "Resolve as chaves substitutas, calcula as medidas e grava", "extrair da entidade"],
            ["validar_carga", "Executa 15 verificações de origem x destino e de integridade", "Grupo fatos (none_failed)"],
            ["houve_alteracao", "Short-circuit: sem escrita no ciclo, encerra a DAG", "validar_carga"],
            ["atualizar_estatisticas", "Executa VACUUM ANALYZE e publica o ativo que aciona os KPIs", "houve_alteracao"],
        ],
        FONTE_PROPRIA, larguras=[4.4, 8.2, 3.4],
    )
    par(doc,
        "Duas DAGs completam o fluxo (Figura 2). A kpi_adventureworks não tem "
        "horário: é acionada pelo ativo publicado ao final da ETL e atualiza "
        "as dez visões em paralelo, de modo que um ciclo sem escrita não "
        "recalcula nada. A simular_movimento_oltp, de disparo manual, aplica "
        "eventos conhecidos na origem e aciona a ETL.")
    figura(
        doc, [DIR_IMAGENS / "dags_auxiliares.png"],
        "DAGs de indicadores e de simulação de movimento",
        "Fonte: captura da interface do Apache Airflow (2026).",
    )
    par(doc,
        "O comportamento incremental foi comprovado em três ciclos, medidos "
        "em meta.etl_execucao (Quadro 3). O ciclo 2 não extraiu nenhuma linha. "
        "Os cerca de 7 segundos dos ciclos 2 e 3 são custo de orquestração, e "
        "não de volume de dados. O ciclo 3 sucedeu os cinco eventos do Quadro "
        "4 e extraiu exatamente as 17 linhas afetadas.")
    quadro(
        doc, "Ciclos de carga executados",
        ["Ciclo", "Cenário", "Extraídas", "Inseridas", "Atualizadas", "Sem alteração", "Duração"],
        [
            ["1", "Carga inicial", "170.525", "170.525", "0", "0 de 10", "42,99 s"],
            ["2", "Sem alterações na origem", "0", "0", "0", "10 de 10", "7,49 s"],
            ["3", "Cinco eventos simulados", "17", "2", "15", "6 de 10", "7,75 s"],
        ],
        "Fonte: elaboração própria a partir de meta.etl_execucao (2026).",
        larguras=[1.0, 4.6, 1.9, 1.9, 2.1, 2.5, 2.0],
    )
    quadro(
        doc, "Efeitos dos eventos simulados na origem",
        ["Evento na origem", "Tratamento", "Efeito observado no DW"],
        [
            ["Preço do produto 707 +10%", "SCD Tipo 2", "Versão 2 a US$ 38,49; as 3.083 vendas antigas seguem na versão 1, a US$ 34,99, e a nova venda aponta para a versão 2"],
            ["Crédito do fornecedor 1492", "SCD Tipo 1", "Linha sobrescrita, com dt_carga preservada"],
            ["Sobrenome do cliente 11000", "Tabela secundária", "Linha atualizada sem que Sales.Customer tenha mudado"],
            ["Envio do pedido 43659 adiado", "Só cabeçalho", "12 linhas de fato atualizadas"],
            ["Pedido novo com dois itens", "Inserção", "Duas linhas novas em fato_vendas"],
        ],
        FONTE_PROPRIA, larguras=[5.0, 2.8, 8.2],
    )
    par(doc,
        "Ao final de cada ciclo, validar_carga compara contagens e somas "
        "entre origem e destino e testa duplicidade, vigências e medidas "
        "derivadas, gravando o resultado em meta.etl_validacao. Todas as 15 "
        "verificações foram aprovadas nos três ciclos; a única diferença "
        "observada, de US$ 0,03 sobre US$ 109,85 milhões, decorre de "
        "arredondamento no recálculo da receita.")


def modelo_dados(doc: Document) -> None:
    subsecao(doc, "2.2", "Modelo de dados")
    par(doc,
        "O modelo proposto (Figura 3) segue o padrão Star Schema, com uma "
        "estrela por processo de negócio: vendas e compras, integradas por "
        "cinco dimensões conformadas (Kimball; Ross, 2013). As 20 chaves "
        "estrangeiras partem sempre de uma fato para uma dimensão, e a "
        "consulta ao catálogo confirmou que nenhuma dimensão referencia outra, "
        "condição que distingue a estrela do Snowflake Schema.")
    par(doc,
        "A granularidade é a mais atômica disponível: cada linha de "
        "fato_vendas representa um item de pedido (Sales.SalesOrderDetail) e "
        "cada linha de fato_compras, um item de ordem de compra "
        "(Purchasing.PurchaseOrderDetail). Nenhuma agregação posterior "
        "recupera um detalhe que o grão descartou (Kimball; Ross, 2013). Os "
        "Quadros 5 e 6 resumem o dicionário de dados; a versão completa, com "
        "todas as colunas, é extraída do catálogo do PostgreSQL e está em "
        "docs/dicionario_dados.md no repositório. Os valores monetários estão "
        "em dólares americanos, moeda-base da AdventureWorks.")
    figura(
        doc, [DIR_DOCS / "modelo_estrela.png"],
        "Modelo multidimensional do Data Warehouse",
        FONTE_PROPRIA,
    )
    quadro(
        doc, "Dicionário de dados: tabelas do modelo",
        ["Tabela (esquema dw)", "Tipo", "Grão ou chave", "Principais atributos", "Linhas"],
        [
            ["fato_vendas", "Fato", "Item de pedido", "12 chaves, receita, custo, número do pedido", "121.317"],
            ["fato_compras", "Fato", "Item de ordem", "8 chaves, quantidades, valor, número da ordem", "8.845"],
            ["dim_tempo", "Conformada", "Data (AAAAMMDD)", "Ano, trimestre, mês, dia da semana", "1.462"],
            ["dim_produto", "Conformada, SCD 2", "Versão do produto", "Hierarquia, preço, custo, vigência", "505"],
            ["dim_funcionario", "Conformada, SCD 1", "Funcionário", "Nome, cargo, papel de vendedor", "291"],
            ["dim_metodo_envio", "Conformada, SCD 1", "Modalidade", "Nome e taxas de frete", "6"],
            ["dim_status_pedido", "Conformada, estática", "Situação", "Domínio, nome, cancelado, concluído", "11"],
            ["dim_cliente", "Vendas, SCD 1", "Cliente", "Tipo (loja ou pessoa), nome, e-mail", "19.821"],
            ["dim_geografia", "Vendas, SCD 1", "Endereço", "Cidade, estado, país, região", "19.615"],
            ["dim_territorio", "Vendas, SCD 1", "Território", "Nome, grupo, país", "11"],
            ["dim_promocao", "Vendas, SCD 1", "Oferta", "Descrição, tipo, percentual", "17"],
            ["dim_canal_venda", "Vendas, estática", "Canal", "Internet ou Revenda", "3"],
            ["dim_fornecedor", "Compras, SCD 1", "Fornecedor", "Nome, nível de crédito, preferencial", "105"],
        ],
        "Fonte: elaboração própria (2026). As contagens são da carga inicial e "
        "incluem o membro −1.",
        larguras=[3.3, 3.2, 2.8, 5.4, 1.3],
    )
    quadro(
        doc, "Dicionário de dados: principais medidas das fatos",
        ["Coluna", "Tipo", "Descrição"],
        [
            ["qt_vendida", "integer", "Unidades vendidas no item (aditiva)"],
            ["vl_bruto", "numeric(19,4)", "qt_vendida × preço unitário, antes do desconto"],
            ["vl_desconto", "numeric(19,4)", "Valor do desconto concedido no item"],
            ["vl_liquido", "numeric(19,4)", "Receita líquida: vl_bruto − vl_desconto"],
            ["vl_custo_total", "numeric(19,4)", "qt_vendida × custo vigente na data do pedido"],
            ["vl_margem_bruta", "numeric(19,4)", "vl_liquido − vl_custo_total"],
            ["vl_frete_rateado", "numeric(19,4)", "Frete do cabeçalho, proporcional à receita da linha"],
            ["qt_recebida, qt_rejeitada", "numeric(12,2)", "Unidades recebidas e recusadas no item de compra"],
            ["vl_total_linha", "numeric(19,4)", "Valor do item da ordem de compra"],
        ],
        FONTE_PROPRIA, larguras=[4.4, 2.6, 9.0],
    )
    quadro(
        doc, "Justificativa das decisões de modelagem",
        ["Decisão", "Justificativa"],
        [
            ["Duas fatos, e não uma", "Vendas e compras têm grãos e medidas incompatíveis; uma tabela única seria esparsa"],
            ["SCD 2 apenas em dim_produto", "Preço e custo evoluem e sua história importa; a de um e-mail, não"],
            ["Dimensão única de funcionários", "Vendedor e comprador são a mesma entidade na origem, em papéis distintos"],
            ["Custo histórico no fato", "Usar o custo atual em venda antiga falsearia a margem do período"],
            ["Rateio de frete e imposto", "Medidas de cabeçalho repetidas no item seriam somadas várias vezes"],
            ["Percentuais como razão de somas", "A média de percentuais ignora o peso de cada linha"],
            ["Membro −1 nas dimensões", "Evita chave nula e torna a ausência de informação mensurável"],
            ["Chave AAAAMMDD em dim_tempo", "Calendário é previsível, e a chave dispensa busca na carga"],
        ],
        FONTE_PROPRIA, larguras=[5.2, 10.8],
    )


def indicadores(doc: Document) -> None:
    subsecao(doc, "2.3", "Indicadores")
    par(doc,
        "Os dez indicadores do Quadro 8 foram implementados em SQL como "
        "visões materializadas do esquema kpi (sql/03_kpis.sql), sem acesso à "
        "base transacional. Dois indicadores do Produto 1 foram substituídos "
        "após o exame dos dados. A pontualidade de entrega não tem variância: "
        "nenhum dos 121.317 itens atrasou, pois o envio ocorre sempre sete ou "
        "oito dias após o pedido. O atingimento de cota compara receitas "
        "anuais de milhões com cotas cadastrais de US$ 250 mil a US$ 300 mil, "
        "o que produziria valores da ordem de 1.000%. Em seu lugar entraram "
        "sazonalidade e recompra por coorte, voltados ao reconhecimento de "
        "padrões. O Quadro 9 traz dois scripts representativos; os demais "
        "estão no repositório.")
    quadro(
        doc, "Indicadores definidos",
        ["#", "Indicador", "Fórmula", "Dimensões"],
        [
            ["01", "Receita líquida", "SUM(vl_liquido)", "Tempo, território"],
            ["02", "Ticket médio e mix", "SUM(vl_liquido) / COUNT(DISTINCT id_pedido)", "Tempo, canal"],
            ["03", "Margem bruta %", "SUM(vl_margem_bruta) / SUM(vl_liquido) × 100", "Tempo, canal, produto"],
            ["04", "Taxa efetiva de desconto", "SUM(vl_desconto) / SUM(vl_bruto) × 100", "Tempo, promoção"],
            ["05", "Crescimento YoY", "(mês − mesmo mês do ano anterior) / anterior × 100", "Tempo"],
            ["06", "Curva ABC", "Receita acumulada / receita total, em ranking", "Produto"],
            ["07", "Índice de sazonalidade", "Receita do mês / média mensal do ano × 100", "Tempo, canal"],
            ["08", "Recompra em 180 dias", "Clientes que voltaram / clientes da coorte × 100", "Tempo, cliente"],
            ["09", "Força de vendas", "Receita do vendedor / receita do ano × 100", "Tempo, funcionário"],
            ["10", "Rejeição por fornecedor", "SUM(qt_rejeitada) / SUM(qt_recebida) × 100", "Tempo, fornecedor, status"],
        ],
        FONTE_PROPRIA, larguras=[0.8, 4.0, 7.4, 3.8],
    )
    quadro_codigo(doc, "Scripts SQL dos indicadores 03 e 06", [
        "-- KPI 03: margem bruta por ano, canal e categoria",
        "SELECT t.nr_ano, c.nm_canal, p.nm_categoria,",
        "       ROUND(100.0 * SUM(f.vl_margem_bruta) / NULLIF(SUM(f.vl_liquido), 0), 2)",
        "           AS pc_margem_bruta",
        "  FROM dw.fato_vendas     AS f",
        "  JOIN dw.dim_tempo       AS t ON t.sk_tempo = f.sk_tempo_pedido",
        "  JOIN dw.dim_canal_venda AS c ON c.sk_canal = f.sk_canal",
        "  JOIN dw.dim_produto     AS p ON p.sk_produto = f.sk_produto",
        " GROUP BY t.nr_ano, c.nm_canal, p.nm_categoria;",
        "",
        "-- KPI 06: curva ABC por função de janela",
        "SELECT *, CASE WHEN pc_acumulado <= 80 THEN 'A'",
        "               WHEN pc_acumulado <= 95 THEN 'B' ELSE 'C' END AS ds_classe_abc",
        "  FROM (SELECT p.nm_produto, SUM(f.vl_liquido) AS vl_receita,",
        "               100.0 * SUM(SUM(f.vl_liquido)) OVER (ORDER BY SUM(f.vl_liquido) DESC",
        "                                                   ROWS UNBOUNDED PRECEDING)",
        "                     / SUM(SUM(f.vl_liquido)) OVER () AS pc_acumulado",
        "          FROM dw.fato_vendas AS f",
        "          JOIN dw.dim_produto AS p ON p.sk_produto = f.sk_produto",
        "         GROUP BY p.nm_produto) AS r;",
    ])


def resultados(doc: Document) -> None:
    subsecao(doc, "2.4", "Resultados dos indicadores")
    par(doc,
        "O Quadro 10 consolida os resultados, apurados na carga inicial, sem "
        "os eventos simulados. A base cobre pedidos de 31/05/2011 a 30/06/2014.")
    quadro(
        doc, "Resultados dos indicadores",
        ["Indicador", "Resultado apurado"],
        [
            ["01 Receita líquida", "US$ 109,85 milhões em 31.465 pedidos; América do Norte com 72,24%"],
            ["02 Ticket médio e mix", "US$ 3.491,07 no geral; Internet US$ 1.061,45 (26,73%), Revenda US$ 21.147,58 (73,27%)"],
            ["03 Margem bruta", "11,43% no geral; Internet 41,15%, Revenda 0,59%"],
            ["04 Taxa de desconto", "0,48% no geral; 35,50% em produtos descontinuados e 17,28% em lançamentos"],
            ["05 Crescimento", "+30,12% de 2012 para 2013, os únicos anos completos"],
            ["06 Curva ABC", "63 produtos (23,68%) somam 79,88% da receita; 137 (51,50%) somam 5,08%"],
            ["07 Sazonalidade", "Internet com pico em novembro (144); Revenda em junho (157), com vale em fevereiro (54)"],
            ["08 Recompra em 180 dias", "Coorte de 2013: lojas 87,02%; pessoas físicas 15,58%"],
            ["09 Força de vendas", "Em 2013, o líder tem 12,50% da receita atribuída e os três primeiros, 37,10%"],
            ["10 Fornecedores", "Rejeição de 3,12%; US$ 62,49 milhões comprados, sem as ordens recusadas"],
        ],
        "Fonte: elaboração própria a partir do Data Warehouse (2026).",
        larguras=[4.2, 11.8],
    )
    par(doc,
        "O padrão mais relevante está na margem. Os 11,43% agregados escondem "
        "dois negócios distintos: a Revenda responde por 73,27% da receita e "
        "apenas 3,80% da margem bruta, com margem negativa em 2013 (−0,83%) e "
        "2014 (−0,24%), enquanto a Internet gera 96,20% da margem com 26,73% "
        "da receita, estável perto de 41% em todos os anos. Esse resultado só "
        "existe porque o custo gravado é o vigente na data do pedido.")
    par(doc,
        "A sazonalidade mostra outro efeito de agregação (Figura 4). Os canais "
        "têm ciclos opostos: a Internet concentra a demanda em novembro e "
        "dezembro, e a Revenda, de junho a setembro, recuando em fevereiro, "
        "abril e novembro, quando faz menos pedidos. O índice total atribui "
        "79 a novembro, justamente o melhor mês da Internet, o que levaria a "
        "uma conclusão errada sobre o consumidor final.")
    figura(
        doc, [DIR_IMAGENS / "sazonalidade_canal.png"],
        "Índice de sazonalidade mensal por canal (anos completos: 2012 e 2013)",
        "Fonte: elaboração própria a partir de kpi.mv_sazonalidade (2026).",
    )
    par(doc,
        "A série também revela uma ruptura estrutural. Acessórios e vestuário "
        "passam a ser vendidos pela Internet em 30/05/2013. A partir daí, os "
        "pedidos totais saltam de 3.915 em 2012 para 14.182 em 2013, o ticket "
        "da Internet cai de US$ 2.329,78 para US$ 852,84 e a recompra de "
        "pessoas físicas sobe de 0,36% para 15,58%. A queda do ticket, lida "
        "isoladamente, pareceria um problema; em conjunto com os demais "
        "indicadores, é compatível com um mix mais amplo. Nas compras, a rejeição "
        "tampouco é um defeito disperso: 142 linhas de ordens recusadas "
        "concentram 64,30% das unidades rejeitadas, e sem elas a taxa cai para "
        "1,14%. A curva ABC, por fim, confirma a concentração de Pareto.")
    par(doc,
        "Os resultados também pedem leitura crítica. Junho de 2014 registra "
        "−99,04% de variação anual porque a base termina nesse mês sem pedidos "
        "de revenda, assim como maio e junho de 2012 se comparam a um 2011 que "
        "mal havia começado. Por isso o crescimento só é citado entre anos "
        "completos.")


def consideracoes(doc: Document) -> None:
    secao(doc, "3", "Considerações finais")
    par(doc,
        "O trabalho atingiu o objetivo proposto: o Data Warehouse foi "
        "implementado em PostgreSQL com modelo Star Schema, a ETL incremental "
        "é orquestrada pelo Apache Airflow e os dez indicadores são calculados "
        "em SQL. A comprovação é empírica: zero linhas extraídas em um ciclo "
        "sem mudanças, exatamente 17 linhas em um ciclo com cinco eventos "
        "conhecidos e 15 verificações aprovadas entre origem e destino.")
    par(doc,
        "Três aprendizados se destacam. A orquestração é mais do que "
        "agendamento: dependências, retentativas, estados ignorados e ativos "
        "tornaram visível, na própria interface, o que cada ciclo fez. A "
        "carga incremental correta exige olhar todas as tabelas que compõem a "
        "entidade e confirmar a marca na mesma transação dos dados. E os "
        "indicadores só ganham sentido quando cruzados: os principais padrões "
        "encontrados estavam ocultos nos totais agregados.")
    par(doc,
        "O trabalho tem limitações. A marca d'água não detecta exclusões "
        "físicas na origem, e uma atualização confirmada tardiamente, com data "
        "anterior à marca, escapa ao filtro; a validação final cobre inserções "
        "perdidas, mas não esse caso. A base é sintética, o que limita "
        "conclusões de negócio, e a configuração do Airflow é de "
        "desenvolvimento. Como continuidade, sugere-se adotar captura de "
        "mudanças por log, modelar uma fato de cotas a partir do histórico "
        "trimestral dos vendedores e criar uma fato de estoque.")


def referencias(doc: Document) -> None:
    secao(doc, "", "Referências")
    itens = [
        [("APACHE SOFTWARE FOUNDATION. ", False), ("Apache Airflow documentation", True),
         (": version 3.3.2. [S. l.]: ASF, 2026. Disponível em: "
          "https://airflow.apache.org/docs/apache-airflow/3.3.2/. Acesso em: 2 nov. 2026.", False)],
        [("CHAUDHURI, S.; DAYAL, U. An overview of data warehousing and OLAP technology. ", False),
         ("ACM SIGMOD Record", True), (", New York, v. 26, n. 1, p. 65-74, mar. 1997.", False)],
        [("INMON, W. H. ", False), ("Building the data warehouse", True),
         (". 4. ed. Indianapolis: Wiley Publishing, 2005.", False)],
        [("KIMBALL, R.; CASERTA, J. ", False), ("The data warehouse ETL toolkit", True),
         (": practical techniques for extracting, cleaning, conforming, and delivering "
          "data. Indianapolis: Wiley Publishing, 2004.", False)],
        [("KIMBALL, R.; ROSS, M. ", False), ("The data warehouse toolkit", True),
         (": the definitive guide to dimensional modeling. 3. ed. Indianapolis: "
          "John Wiley & Sons, 2013.", False)],
        [("MICROSOFT. ", False), ("AdventureWorks sample databases", True),
         (". [S. l.]: Microsoft Learn, 2024. Disponível em: https://learn.microsoft.com/"
          "pt-br/sql/samples/adventureworks-install-configure. Acesso em: 2 nov. 2026.", False)],
        [("SANTOS, Yahn de Freitas. ", False), ("dw-adventureworks-produto1", True),
         (": ETL incremental e Data Warehouse dimensional para a base AdventureWorks. "
          "Vitória: [s. n.], 2026a. Repositório de código. Disponível em: "
          "https://github.com/Yahnfs/dw-adventureworks-produto1. Acesso em: 2 nov. 2026.", False)],
        [("SANTOS, Yahn de Freitas. ", False), ("dw-adventureworks-airflow", True),
         (": Data Warehouse AdventureWorks orquestrado com Apache Airflow. Vitória: "
          f"[s. n.], 2026b. Repositório de código. Disponível em: {REPOSITORIO}. "
          "Acesso em: 2 nov. 2026.", False)],
        [("VAISMAN, A.; ZIMÁNYI, E. ", False), ("Data warehouse systems", True),
         (": design and implementation. 2. ed. Berlin: Springer, 2022.", False)],
    ]
    for item in itens:
        referencia(doc, item)


def montar() -> Path:
    _contadores["quadro"] = _contadores["figura"] = 0
    doc = configurar_documento()
    pre_textuais(doc)
    introducao(doc)
    secao(doc, "2", "Desenvolvimento")
    par(doc,
        "Esta seção descreve o processo de ETL e sua orquestração, o modelo "
        "de dados, os indicadores definidos e os resultados obtidos.")
    data_etl(doc)
    modelo_dados(doc)
    indicadores(doc)
    resultados(doc)
    consideracoes(doc)
    referencias(doc)

    propriedades = doc.core_properties
    propriedades.title = "Orquestração de um Data Warehouse com Apache Airflow"
    propriedades.author = "Yahn de Freitas Santos"
    propriedades.last_modified_by = "Yahn de Freitas Santos"
    propriedades.comments = ""

    doc.save(SAIDA)
    return SAIDA


if __name__ == "__main__":
    print(f"Artigo gerado em: {montar()}")
