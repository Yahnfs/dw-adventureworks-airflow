"""Transformacoes SQL que promovem os dados de ``stg`` para ``dw``.

Todo comando desta camada e idempotente. Reexecutar a mesma janela de
extracao produz exatamente o mesmo estado final do Data Warehouse, o que
permite reprocessar cargas com seguranca apos qualquer falha.

Padroes empregados:

* Dimensoes SCD Tipo 1 -- ``INSERT ... ON CONFLICT (chave_natural) DO UPDATE``
  condicionado a alteracao do ``hash_scd``. Linhas inalteradas nao sofrem
  escrita, o que evita inflar o WAL e mantem ``dt_atualizacao`` fiel.
* Dimensao SCD Tipo 2 (produto) -- comparacao de hash, encerramento da versao
  vigente e insercao da nova versao, em comandos sequenciais dentro da mesma
  transacao.
* Fatos -- ``INSERT ... ON CONFLICT (chave_degenerada) DO UPDATE``, com o
  predicado ``dt_modificacao_origem <= EXCLUDED.dt_modificacao_origem`` para
  que uma reexecucao jamais sobrescreva um dado mais novo por um mais antigo.

O truque ``xmax = 0`` no ``RETURNING`` distingue insercoes de atualizacoes:
em uma linha recem-inserida o campo de sistema ``xmax`` vale zero.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# DIMENSOES SCD TIPO 1
# ---------------------------------------------------------------------------

CLIENTE = """
WITH origem AS (
    SELECT DISTINCT ON (id_cliente)
           id_cliente, cd_conta, tp_cliente, nm_cliente, nm_primeiro,
           nm_sobrenome, nm_loja, ds_email,
           COALESCE(fl_aceita_promocao, FALSE) AS fl_aceita_promocao,
           dt_modificacao_origem,
           md5(concat_ws('|', cd_conta, tp_cliente, nm_cliente, nm_primeiro,
                              nm_sobrenome, nm_loja, ds_email,
                              COALESCE(fl_aceita_promocao, FALSE))) AS hash_novo
      FROM stg.cliente
     ORDER BY id_cliente, dt_modificacao_origem DESC
)
INSERT INTO dw.dim_cliente AS d (
    id_cliente, cd_conta, tp_cliente, nm_cliente, nm_primeiro, nm_sobrenome,
    nm_loja, ds_email, fl_aceita_promocao, hash_scd, dt_modificacao_origem)
SELECT id_cliente, cd_conta, tp_cliente, nm_cliente, nm_primeiro, nm_sobrenome,
       nm_loja, ds_email, fl_aceita_promocao, hash_novo, dt_modificacao_origem
  FROM origem
ON CONFLICT (id_cliente) DO UPDATE
   SET cd_conta              = EXCLUDED.cd_conta,
       tp_cliente            = EXCLUDED.tp_cliente,
       nm_cliente            = EXCLUDED.nm_cliente,
       nm_primeiro           = EXCLUDED.nm_primeiro,
       nm_sobrenome          = EXCLUDED.nm_sobrenome,
       nm_loja               = EXCLUDED.nm_loja,
       ds_email              = EXCLUDED.ds_email,
       fl_aceita_promocao    = EXCLUDED.fl_aceita_promocao,
       hash_scd              = EXCLUDED.hash_scd,
       dt_modificacao_origem = EXCLUDED.dt_modificacao_origem,
       dt_atualizacao        = CURRENT_TIMESTAMP
 WHERE d.hash_scd IS DISTINCT FROM EXCLUDED.hash_scd
RETURNING (xmax = 0) AS inserido;
"""

FUNCIONARIO = """
WITH origem AS (
    SELECT DISTINCT ON (id_funcionario)
           id_funcionario, nm_funcionario, ds_cargo, ds_genero, ds_estado_civil,
           dt_nascimento, dt_admissao, fl_assalariado,
           COALESCE(fl_vendedor, FALSE) AS fl_vendedor,
           vl_cota_vendas, vl_bonus, pc_comissao, dt_modificacao_origem,
           md5(concat_ws('|', nm_funcionario, ds_cargo, ds_genero, ds_estado_civil,
                              dt_nascimento, dt_admissao, fl_assalariado,
                              COALESCE(fl_vendedor, FALSE), vl_cota_vendas,
                              vl_bonus, pc_comissao)) AS hash_novo
      FROM stg.funcionario
     ORDER BY id_funcionario, dt_modificacao_origem DESC
)
INSERT INTO dw.dim_funcionario AS d (
    id_funcionario, nm_funcionario, ds_cargo, ds_genero, ds_estado_civil,
    dt_nascimento, dt_admissao, fl_assalariado, fl_vendedor, vl_cota_vendas,
    vl_bonus, pc_comissao, hash_scd, dt_modificacao_origem)
SELECT id_funcionario, nm_funcionario, ds_cargo, ds_genero, ds_estado_civil,
       dt_nascimento, dt_admissao, fl_assalariado, fl_vendedor, vl_cota_vendas,
       vl_bonus, pc_comissao, hash_novo, dt_modificacao_origem
  FROM origem
ON CONFLICT (id_funcionario) DO UPDATE
   SET nm_funcionario        = EXCLUDED.nm_funcionario,
       ds_cargo              = EXCLUDED.ds_cargo,
       ds_genero             = EXCLUDED.ds_genero,
       ds_estado_civil       = EXCLUDED.ds_estado_civil,
       dt_nascimento         = EXCLUDED.dt_nascimento,
       dt_admissao           = EXCLUDED.dt_admissao,
       fl_assalariado        = EXCLUDED.fl_assalariado,
       fl_vendedor           = EXCLUDED.fl_vendedor,
       vl_cota_vendas        = EXCLUDED.vl_cota_vendas,
       vl_bonus              = EXCLUDED.vl_bonus,
       pc_comissao           = EXCLUDED.pc_comissao,
       hash_scd              = EXCLUDED.hash_scd,
       dt_modificacao_origem = EXCLUDED.dt_modificacao_origem,
       dt_atualizacao        = CURRENT_TIMESTAMP
 WHERE d.hash_scd IS DISTINCT FROM EXCLUDED.hash_scd
RETURNING (xmax = 0) AS inserido;
"""

TERRITORIO = """
WITH origem AS (
    SELECT DISTINCT ON (id_territorio)
           id_territorio, nm_territorio, nm_grupo, cd_pais, nm_pais,
           vl_vendas_ano_atual, vl_vendas_ano_ante, vl_custo_ano_atual,
           dt_modificacao_origem,
           md5(concat_ws('|', nm_territorio, nm_grupo, cd_pais, nm_pais,
                              vl_vendas_ano_atual, vl_vendas_ano_ante,
                              vl_custo_ano_atual)) AS hash_novo
      FROM stg.territorio
     ORDER BY id_territorio, dt_modificacao_origem DESC
)
INSERT INTO dw.dim_territorio AS d (
    id_territorio, nm_territorio, nm_grupo, cd_pais, nm_pais,
    vl_vendas_ano_atual, vl_vendas_ano_ante, vl_custo_ano_atual,
    hash_scd, dt_modificacao_origem)
SELECT id_territorio, nm_territorio, nm_grupo, cd_pais, nm_pais,
       vl_vendas_ano_atual, vl_vendas_ano_ante, vl_custo_ano_atual,
       hash_novo, dt_modificacao_origem
  FROM origem
ON CONFLICT (id_territorio) DO UPDATE
   SET nm_territorio         = EXCLUDED.nm_territorio,
       nm_grupo              = EXCLUDED.nm_grupo,
       cd_pais               = EXCLUDED.cd_pais,
       nm_pais               = EXCLUDED.nm_pais,
       vl_vendas_ano_atual   = EXCLUDED.vl_vendas_ano_atual,
       vl_vendas_ano_ante    = EXCLUDED.vl_vendas_ano_ante,
       vl_custo_ano_atual    = EXCLUDED.vl_custo_ano_atual,
       hash_scd              = EXCLUDED.hash_scd,
       dt_modificacao_origem = EXCLUDED.dt_modificacao_origem,
       dt_atualizacao        = CURRENT_TIMESTAMP
 WHERE d.hash_scd IS DISTINCT FROM EXCLUDED.hash_scd
RETURNING (xmax = 0) AS inserido;
"""

GEOGRAFIA = """
WITH origem AS (
    SELECT DISTINCT ON (id_endereco)
           id_endereco, ds_cidade, cd_estado, nm_estado, cd_pais, nm_pais,
           nm_regiao, cd_postal, dt_modificacao_origem,
           md5(concat_ws('|', ds_cidade, cd_estado, nm_estado, cd_pais,
                              nm_pais, nm_regiao, cd_postal)) AS hash_novo
      FROM stg.geografia
     ORDER BY id_endereco, dt_modificacao_origem DESC
)
INSERT INTO dw.dim_geografia AS d (
    id_endereco, ds_cidade, cd_estado, nm_estado, cd_pais, nm_pais,
    nm_regiao, cd_postal, hash_scd, dt_modificacao_origem)
SELECT id_endereco, ds_cidade, cd_estado, nm_estado, cd_pais, nm_pais,
       nm_regiao, cd_postal, hash_novo, dt_modificacao_origem
  FROM origem
ON CONFLICT (id_endereco) DO UPDATE
   SET ds_cidade             = EXCLUDED.ds_cidade,
       cd_estado             = EXCLUDED.cd_estado,
       nm_estado             = EXCLUDED.nm_estado,
       cd_pais               = EXCLUDED.cd_pais,
       nm_pais               = EXCLUDED.nm_pais,
       nm_regiao             = EXCLUDED.nm_regiao,
       cd_postal             = EXCLUDED.cd_postal,
       hash_scd              = EXCLUDED.hash_scd,
       dt_modificacao_origem = EXCLUDED.dt_modificacao_origem,
       dt_atualizacao        = CURRENT_TIMESTAMP
 WHERE d.hash_scd IS DISTINCT FROM EXCLUDED.hash_scd
RETURNING (xmax = 0) AS inserido;
"""

FORNECEDOR = """
WITH origem AS (
    SELECT DISTINCT ON (id_fornecedor)
           id_fornecedor, cd_conta, nm_fornecedor, nr_nivel_credito,
           COALESCE(fl_fornecedor_ativo, TRUE)  AS fl_fornecedor_ativo,
           COALESCE(fl_preferencial, FALSE)     AS fl_preferencial,
           dt_modificacao_origem,
           md5(concat_ws('|', cd_conta, nm_fornecedor, nr_nivel_credito,
                              COALESCE(fl_fornecedor_ativo, TRUE),
                              COALESCE(fl_preferencial, FALSE))) AS hash_novo
      FROM stg.fornecedor
     ORDER BY id_fornecedor, dt_modificacao_origem DESC
)
INSERT INTO dw.dim_fornecedor AS d (
    id_fornecedor, cd_conta, nm_fornecedor, nr_nivel_credito, ds_nivel_credito,
    fl_fornecedor_ativo, fl_preferencial, hash_scd, dt_modificacao_origem)
SELECT id_fornecedor, cd_conta, nm_fornecedor, nr_nivel_credito,
       CASE nr_nivel_credito
            WHEN 1 THEN 'Superior' WHEN 2 THEN 'Excelente'
            WHEN 3 THEN 'Acima da Media' WHEN 4 THEN 'Media'
            WHEN 5 THEN 'Abaixo da Media'
            ELSE 'Nao Informado' END,
       fl_fornecedor_ativo, fl_preferencial, hash_novo, dt_modificacao_origem
  FROM origem
ON CONFLICT (id_fornecedor) DO UPDATE
   SET cd_conta              = EXCLUDED.cd_conta,
       nm_fornecedor         = EXCLUDED.nm_fornecedor,
       nr_nivel_credito      = EXCLUDED.nr_nivel_credito,
       ds_nivel_credito      = EXCLUDED.ds_nivel_credito,
       fl_fornecedor_ativo   = EXCLUDED.fl_fornecedor_ativo,
       fl_preferencial       = EXCLUDED.fl_preferencial,
       hash_scd              = EXCLUDED.hash_scd,
       dt_modificacao_origem = EXCLUDED.dt_modificacao_origem,
       dt_atualizacao        = CURRENT_TIMESTAMP
 WHERE d.hash_scd IS DISTINCT FROM EXCLUDED.hash_scd
RETURNING (xmax = 0) AS inserido;
"""

PROMOCAO = """
WITH origem AS (
    SELECT DISTINCT ON (id_promocao)
           id_promocao, ds_promocao, tp_promocao, ds_categoria,
           COALESCE(pc_desconto, 0) AS pc_desconto,
           qt_minima, qt_maxima, dt_inicio, dt_fim, dt_modificacao_origem,
           md5(concat_ws('|', ds_promocao, tp_promocao, ds_categoria,
                              COALESCE(pc_desconto, 0), qt_minima, qt_maxima,
                              dt_inicio, dt_fim)) AS hash_novo
      FROM stg.promocao
     ORDER BY id_promocao, dt_modificacao_origem DESC
)
INSERT INTO dw.dim_promocao AS d (
    id_promocao, ds_promocao, tp_promocao, ds_categoria, pc_desconto,
    qt_minima, qt_maxima, dt_inicio, dt_fim, fl_com_desconto,
    hash_scd, dt_modificacao_origem)
SELECT id_promocao, ds_promocao, tp_promocao, ds_categoria, pc_desconto,
       qt_minima, qt_maxima, dt_inicio, dt_fim, (pc_desconto > 0),
       hash_novo, dt_modificacao_origem
  FROM origem
ON CONFLICT (id_promocao) DO UPDATE
   SET ds_promocao           = EXCLUDED.ds_promocao,
       tp_promocao           = EXCLUDED.tp_promocao,
       ds_categoria          = EXCLUDED.ds_categoria,
       pc_desconto           = EXCLUDED.pc_desconto,
       qt_minima             = EXCLUDED.qt_minima,
       qt_maxima             = EXCLUDED.qt_maxima,
       dt_inicio             = EXCLUDED.dt_inicio,
       dt_fim                = EXCLUDED.dt_fim,
       fl_com_desconto       = EXCLUDED.fl_com_desconto,
       hash_scd              = EXCLUDED.hash_scd,
       dt_modificacao_origem = EXCLUDED.dt_modificacao_origem,
       dt_atualizacao        = CURRENT_TIMESTAMP
 WHERE d.hash_scd IS DISTINCT FROM EXCLUDED.hash_scd
RETURNING (xmax = 0) AS inserido;
"""

METODO_ENVIO = """
WITH origem AS (
    SELECT DISTINCT ON (id_metodo_envio)
           id_metodo_envio, nm_metodo_envio, vl_taxa_base, vl_taxa_por_peso,
           dt_modificacao_origem,
           md5(concat_ws('|', nm_metodo_envio, vl_taxa_base, vl_taxa_por_peso)) AS hash_novo
      FROM stg.metodo_envio
     ORDER BY id_metodo_envio, dt_modificacao_origem DESC
)
INSERT INTO dw.dim_metodo_envio AS d (
    id_metodo_envio, nm_metodo_envio, vl_taxa_base, vl_taxa_por_peso,
    hash_scd, dt_modificacao_origem)
SELECT id_metodo_envio, nm_metodo_envio, vl_taxa_base, vl_taxa_por_peso,
       hash_novo, dt_modificacao_origem
  FROM origem
ON CONFLICT (id_metodo_envio) DO UPDATE
   SET nm_metodo_envio       = EXCLUDED.nm_metodo_envio,
       vl_taxa_base          = EXCLUDED.vl_taxa_base,
       vl_taxa_por_peso      = EXCLUDED.vl_taxa_por_peso,
       hash_scd              = EXCLUDED.hash_scd,
       dt_modificacao_origem = EXCLUDED.dt_modificacao_origem,
       dt_atualizacao        = CURRENT_TIMESTAMP
 WHERE d.hash_scd IS DISTINCT FROM EXCLUDED.hash_scd
RETURNING (xmax = 0) AS inserido;
"""

SCD1 = {
    "dim_cliente": CLIENTE,
    "dim_funcionario": FUNCIONARIO,
    "dim_territorio": TERRITORIO,
    "dim_geografia": GEOGRAFIA,
    "dim_fornecedor": FORNECEDOR,
    "dim_promocao": PROMOCAO,
    "dim_metodo_envio": METODO_ENVIO,
}


# ---------------------------------------------------------------------------
# DIMENSAO PRODUTO -- SCD TIPO 2
#
# Executada em tres passos sequenciais na mesma transacao, e nao em uma unica
# instrucao com CTEs modificadoras: no PostgreSQL todas as sub-instrucoes de
# uma mesma instrucao enxergam o mesmo instantaneo (snapshot) e a ordem de
# execucao nao e garantida, o que colocaria o encerramento da versao vigente
# e a insercao da nova versao em disputa pelo indice unico parcial
# ux_dim_produto_corrente.
# ---------------------------------------------------------------------------

PRODUTO_SCD2_DETECTAR = """
CREATE TEMPORARY TABLE tmp_produto_alterado ON COMMIT DROP AS
WITH origem AS (
    SELECT DISTINCT ON (id_produto)
           s.*,
           md5(concat_ws('|', s.cd_produto, s.nm_produto, s.nm_categoria,
                              s.nm_subcategoria, s.nm_modelo, s.ds_linha,
                              s.ds_classe, s.ds_estilo, s.ds_cor, s.ds_tamanho,
                              s.vl_peso, s.nm_unidade_peso, s.vl_custo_padrao,
                              s.vl_preco_lista, s.fl_fabricacao_propria,
                              s.fl_produto_acabado, s.qt_estoque_seguranca,
                              s.qt_ponto_reposicao, s.nr_dias_fabricacao,
                              s.dt_inicio_venda, s.dt_fim_venda,
                              s.dt_descontinuado)) AS hash_novo
      FROM stg.produto AS s
     ORDER BY s.id_produto, s.dt_modificacao_origem DESC
)
SELECT o.*,
       d.sk_produto        AS sk_vigente,
       d.nr_versao         AS nr_versao_vigente,
       d.dt_inicio_validade AS dt_inicio_vigente
  FROM origem AS o
  LEFT JOIN dw.dim_produto AS d
         ON d.id_produto = o.id_produto AND d.fl_corrente
 WHERE d.sk_produto IS NULL
    OR d.hash_scd IS DISTINCT FROM o.hash_novo;
"""

# Encerra a versao vigente na vespera do inicio da nova versao. GREATEST
# impede que o intervalo fique invertido quando duas alteracoes ocorrem no
# mesmo dia (nesse caso a versao anterior vigora por zero dia).
PRODUTO_SCD2_ENCERRAR = """
UPDATE dw.dim_produto AS d
   SET fl_corrente     = FALSE,
       dt_fim_validade = GREATEST(
           d.dt_inicio_validade,
           COALESCE(t.dt_modificacao_origem::date, CURRENT_DATE) - INTERVAL '1 day'
       )::date,
       dt_atualizacao  = CURRENT_TIMESTAMP
  FROM tmp_produto_alterado AS t
 WHERE d.sk_produto = t.sk_vigente
   AND t.sk_vigente IS NOT NULL;
"""

PRODUTO_SCD2_INSERIR = """
INSERT INTO dw.dim_produto (
    id_produto, cd_produto, nm_produto, nm_categoria, nm_subcategoria,
    nm_modelo, ds_linha, ds_classe, ds_estilo, ds_cor, ds_tamanho, vl_peso,
    nm_unidade_peso, vl_custo_padrao, vl_preco_lista, fl_fabricacao_propria,
    fl_produto_acabado, qt_estoque_seguranca, qt_ponto_reposicao,
    nr_dias_fabricacao, dt_inicio_venda, dt_fim_venda, dt_descontinuado,
    nr_versao, dt_inicio_validade, dt_fim_validade, fl_corrente, hash_scd,
    dt_modificacao_origem)
SELECT t.id_produto, t.cd_produto, t.nm_produto,
       COALESCE(t.nm_categoria, 'Sem Categoria'),
       COALESCE(t.nm_subcategoria, 'Sem Subcategoria'),
       COALESCE(t.nm_modelo, 'Sem Modelo'),
       COALESCE(t.ds_linha, 'Nao Informado'),
       COALESCE(t.ds_classe, 'Nao Informado'),
       COALESCE(t.ds_estilo, 'Nao Informado'),
       COALESCE(t.ds_cor, 'Nao Informado'),
       t.ds_tamanho, t.vl_peso, t.nm_unidade_peso,
       COALESCE(t.vl_custo_padrao, 0), COALESCE(t.vl_preco_lista, 0),
       COALESCE(t.fl_fabricacao_propria, FALSE),
       COALESCE(t.fl_produto_acabado, FALSE),
       t.qt_estoque_seguranca, t.qt_ponto_reposicao, t.nr_dias_fabricacao,
       t.dt_inicio_venda, t.dt_fim_venda, t.dt_descontinuado,
       COALESCE(t.nr_versao_vigente, 0) + 1,
       -- A primeira versao vigora desde sempre, para que nenhum fato
       -- historico deixe de encontrar a versao correspondente do produto.
       CASE WHEN t.sk_vigente IS NULL
            THEN DATE '1900-01-01'
            ELSE COALESCE(t.dt_modificacao_origem::date, CURRENT_DATE)
       END,
       DATE '9999-12-31', TRUE, t.hash_novo, t.dt_modificacao_origem
  FROM tmp_produto_alterado AS t
RETURNING (xmax = 0) AS inserido;
"""


# ---------------------------------------------------------------------------
# FATOS
#
# A busca da chave substituta do produto respeita a vigencia SCD Tipo 2: usa-se
# a versao valida na data do pedido. O LATERAL fica com a versao mais recente,
# porque duas alteracoes no mesmo dia geram vigencias que se tocam nessa data e
# um JOIN comum duplicaria a linha do fato. O segundo LEFT JOIN (versao
# corrente) e a rede de seguranca para pedidos cuja data caia fora de qualquer
# intervalo, e o COALESCE final direciona ao membro "Nao Informado" (-1) o que
# ainda assim nao for resolvido.
#
# Frete e imposto sao rateados entre as linhas do pedido na proporcao da
# receita liquida de cada linha sobre o subtotal do cabecalho. Sem esse rateio
# as medidas do cabecalho seriam contadas varias vezes ao serem somadas no
# grao de item, distorcendo qualquer agregacao.
# ---------------------------------------------------------------------------

FATO_VENDAS = """
WITH origem AS (
    SELECT DISTINCT ON (id_item_venda) *
      FROM stg.venda_item
     ORDER BY id_item_venda, dt_modificacao_origem DESC
),
calculado AS (
    SELECT o.*,
           (o.qt_vendida * o.vl_preco_unitario)                              AS vl_bruto,
           (o.qt_vendida * o.vl_preco_unitario * COALESCE(o.pc_desconto_unitario, 0)) AS vl_desconto,
           (o.qt_vendida * o.vl_preco_unitario
              * (1 - COALESCE(o.pc_desconto_unitario, 0)))                   AS vl_liquido,
           (o.qt_vendida * COALESCE(o.vl_custo_unitario, 0))                 AS vl_custo_total
      FROM origem AS o
)
INSERT INTO dw.fato_vendas AS f (
    sk_tempo_pedido, sk_tempo_vencimento, sk_tempo_envio, sk_produto,
    sk_cliente, sk_vendedor, sk_territorio, sk_promocao, sk_geografia_entrega,
    sk_metodo_envio, sk_canal, sk_status, id_item_venda, id_pedido, nr_pedido,
    nr_pedido_cliente, qt_vendida, vl_preco_unitario, pc_desconto_unitario,
    vl_bruto, vl_desconto, vl_liquido, vl_custo_unitario, vl_custo_total,
    vl_margem_bruta, vl_frete_rateado, vl_imposto_rateado, qt_dias_entrega,
    qt_dias_atraso, fl_entrega_atrasada, fl_pedido_online, dt_modificacao_origem)
SELECT
    COALESCE(tpd.sk_tempo, -1),
    COALESCE(tvc.sk_tempo, -1),
    COALESCE(tev.sk_tempo, -1),
    COALESCE(prd_vig.sk_produto, prd_cor.sk_produto, -1),
    COALESCE(cli.sk_cliente, -1),
    COALESCE(vnd.sk_funcionario, -1),
    COALESCE(ter.sk_territorio, -1),
    COALESCE(pro.sk_promocao, -1),
    COALESCE(geo.sk_geografia, -1),
    COALESCE(env.sk_metodo_envio, -1),
    CASE WHEN c.fl_pedido_online IS TRUE THEN 1
         WHEN c.fl_pedido_online IS FALSE THEN 2 ELSE -1 END,
    COALESCE(sts.sk_status, -1),
    c.id_item_venda,
    c.id_pedido,
    c.nr_pedido,
    c.nr_pedido_cliente,
    c.qt_vendida,
    c.vl_preco_unitario,
    COALESCE(c.pc_desconto_unitario, 0),
    c.vl_bruto,
    c.vl_desconto,
    c.vl_liquido,
    COALESCE(c.vl_custo_unitario, 0),
    c.vl_custo_total,
    c.vl_liquido - c.vl_custo_total,
    ROUND(COALESCE(c.vl_frete_pedido, 0)
          * (c.vl_liquido / NULLIF(c.vl_subtotal_pedido, 0)), 4),
    ROUND(COALESCE(c.vl_imposto_pedido, 0)
          * (c.vl_liquido / NULLIF(c.vl_subtotal_pedido, 0)), 4),
    (c.dt_envio - c.dt_pedido),
    GREATEST(c.dt_envio - c.dt_vencimento, 0),
    (c.dt_envio IS NOT NULL AND c.dt_vencimento IS NOT NULL
     AND c.dt_envio > c.dt_vencimento),
    COALESCE(c.fl_pedido_online, FALSE),
    c.dt_modificacao_origem
FROM calculado AS c
LEFT JOIN dw.dim_tempo        AS tpd ON tpd.dt_data = c.dt_pedido
LEFT JOIN dw.dim_tempo        AS tvc ON tvc.dt_data = c.dt_vencimento
LEFT JOIN dw.dim_tempo        AS tev ON tev.dt_data = c.dt_envio
LEFT JOIN LATERAL (
    SELECT p.sk_produto
      FROM dw.dim_produto AS p
     WHERE p.id_produto = c.id_produto
       AND c.dt_pedido BETWEEN p.dt_inicio_validade AND p.dt_fim_validade
     ORDER BY p.nr_versao DESC
     LIMIT 1
) AS prd_vig ON TRUE
LEFT JOIN dw.dim_produto      AS prd_cor ON prd_cor.id_produto = c.id_produto
                                        AND prd_cor.fl_corrente
LEFT JOIN dw.dim_cliente      AS cli ON cli.id_cliente      = c.id_cliente
LEFT JOIN dw.dim_funcionario  AS vnd ON vnd.id_funcionario  = c.id_vendedor
LEFT JOIN dw.dim_territorio   AS ter ON ter.id_territorio   = c.id_territorio
LEFT JOIN dw.dim_promocao     AS pro ON pro.id_promocao     = c.id_promocao
LEFT JOIN dw.dim_geografia    AS geo ON geo.id_endereco     = c.id_endereco_entrega
LEFT JOIN dw.dim_metodo_envio AS env ON env.id_metodo_envio = c.id_metodo_envio
LEFT JOIN dw.dim_status_pedido AS sts ON sts.cd_status = c.cd_status
                                     AND sts.ds_dominio = 'VENDA'
ON CONFLICT (id_item_venda) DO UPDATE
   SET sk_tempo_pedido       = EXCLUDED.sk_tempo_pedido,
       sk_tempo_vencimento   = EXCLUDED.sk_tempo_vencimento,
       sk_tempo_envio        = EXCLUDED.sk_tempo_envio,
       sk_produto            = EXCLUDED.sk_produto,
       sk_cliente            = EXCLUDED.sk_cliente,
       sk_vendedor           = EXCLUDED.sk_vendedor,
       sk_territorio         = EXCLUDED.sk_territorio,
       sk_promocao           = EXCLUDED.sk_promocao,
       sk_geografia_entrega  = EXCLUDED.sk_geografia_entrega,
       sk_metodo_envio       = EXCLUDED.sk_metodo_envio,
       sk_canal              = EXCLUDED.sk_canal,
       sk_status             = EXCLUDED.sk_status,
       nr_pedido             = EXCLUDED.nr_pedido,
       nr_pedido_cliente     = EXCLUDED.nr_pedido_cliente,
       qt_vendida            = EXCLUDED.qt_vendida,
       vl_preco_unitario     = EXCLUDED.vl_preco_unitario,
       pc_desconto_unitario  = EXCLUDED.pc_desconto_unitario,
       vl_bruto              = EXCLUDED.vl_bruto,
       vl_desconto           = EXCLUDED.vl_desconto,
       vl_liquido            = EXCLUDED.vl_liquido,
       vl_custo_unitario     = EXCLUDED.vl_custo_unitario,
       vl_custo_total        = EXCLUDED.vl_custo_total,
       vl_margem_bruta       = EXCLUDED.vl_margem_bruta,
       vl_frete_rateado      = EXCLUDED.vl_frete_rateado,
       vl_imposto_rateado    = EXCLUDED.vl_imposto_rateado,
       qt_dias_entrega       = EXCLUDED.qt_dias_entrega,
       qt_dias_atraso        = EXCLUDED.qt_dias_atraso,
       fl_entrega_atrasada   = EXCLUDED.fl_entrega_atrasada,
       fl_pedido_online      = EXCLUDED.fl_pedido_online,
       dt_modificacao_origem = EXCLUDED.dt_modificacao_origem,
       dt_atualizacao        = CURRENT_TIMESTAMP
 WHERE f.dt_modificacao_origem <= EXCLUDED.dt_modificacao_origem
RETURNING (xmax = 0) AS inserido;
"""

FATO_COMPRAS = """
WITH origem AS (
    SELECT DISTINCT ON (id_item_compra) *
      FROM stg.compra_item
     ORDER BY id_item_compra, dt_modificacao_origem DESC
)
INSERT INTO dw.fato_compras AS f (
    sk_tempo_pedido, sk_tempo_previsto, sk_tempo_recebimento, sk_produto,
    sk_fornecedor, sk_comprador, sk_metodo_envio, sk_status, id_item_compra,
    id_ordem_compra, qt_pedida, qt_recebida, qt_rejeitada, qt_aceita,
    vl_preco_unitario, vl_total_linha, vl_frete_rateado, vl_imposto_rateado,
    qt_dias_recebimento, qt_dias_atraso, fl_recebimento_atrasado,
    dt_modificacao_origem)
SELECT
    COALESCE(tpd.sk_tempo, -1),
    COALESCE(tpv.sk_tempo, -1),
    COALESCE(trc.sk_tempo, -1),
    COALESCE(prd_vig.sk_produto, prd_cor.sk_produto, -1),
    COALESCE(frn.sk_fornecedor, -1),
    COALESCE(cmp.sk_funcionario, -1),
    COALESCE(env.sk_metodo_envio, -1),
    COALESCE(sts.sk_status, -1),
    o.id_item_compra,
    o.id_ordem_compra,
    o.qt_pedida,
    COALESCE(o.qt_recebida, 0),
    COALESCE(o.qt_rejeitada, 0),
    COALESCE(o.qt_recebida, 0) - COALESCE(o.qt_rejeitada, 0),
    o.vl_preco_unitario,
    o.vl_total_linha,
    ROUND(COALESCE(o.vl_frete_pedido, 0)
          * (o.vl_total_linha / NULLIF(o.vl_subtotal_pedido, 0)), 4),
    ROUND(COALESCE(o.vl_imposto_pedido, 0)
          * (o.vl_total_linha / NULLIF(o.vl_subtotal_pedido, 0)), 4),
    (o.dt_envio - o.dt_pedido),
    GREATEST(o.dt_envio - o.dt_previsto, 0),
    (o.dt_envio IS NOT NULL AND o.dt_previsto IS NOT NULL
     AND o.dt_envio > o.dt_previsto),
    o.dt_modificacao_origem
FROM origem AS o
LEFT JOIN dw.dim_tempo        AS tpd ON tpd.dt_data = o.dt_pedido
LEFT JOIN dw.dim_tempo        AS tpv ON tpv.dt_data = o.dt_previsto
LEFT JOIN dw.dim_tempo        AS trc ON trc.dt_data = o.dt_envio
LEFT JOIN LATERAL (
    SELECT p.sk_produto
      FROM dw.dim_produto AS p
     WHERE p.id_produto = o.id_produto
       AND o.dt_pedido BETWEEN p.dt_inicio_validade AND p.dt_fim_validade
     ORDER BY p.nr_versao DESC
     LIMIT 1
) AS prd_vig ON TRUE
LEFT JOIN dw.dim_produto      AS prd_cor ON prd_cor.id_produto = o.id_produto
                                        AND prd_cor.fl_corrente
LEFT JOIN dw.dim_fornecedor   AS frn ON frn.id_fornecedor   = o.id_fornecedor
LEFT JOIN dw.dim_funcionario  AS cmp ON cmp.id_funcionario  = o.id_comprador
LEFT JOIN dw.dim_metodo_envio AS env ON env.id_metodo_envio = o.id_metodo_envio
LEFT JOIN dw.dim_status_pedido AS sts ON sts.cd_status = o.cd_status
                                     AND sts.ds_dominio = 'COMPRA'
ON CONFLICT (id_item_compra) DO UPDATE
   SET sk_tempo_pedido        = EXCLUDED.sk_tempo_pedido,
       sk_tempo_previsto      = EXCLUDED.sk_tempo_previsto,
       sk_tempo_recebimento   = EXCLUDED.sk_tempo_recebimento,
       sk_produto             = EXCLUDED.sk_produto,
       sk_fornecedor          = EXCLUDED.sk_fornecedor,
       sk_comprador           = EXCLUDED.sk_comprador,
       sk_metodo_envio        = EXCLUDED.sk_metodo_envio,
       sk_status              = EXCLUDED.sk_status,
       qt_pedida              = EXCLUDED.qt_pedida,
       qt_recebida            = EXCLUDED.qt_recebida,
       qt_rejeitada           = EXCLUDED.qt_rejeitada,
       qt_aceita              = EXCLUDED.qt_aceita,
       vl_preco_unitario      = EXCLUDED.vl_preco_unitario,
       vl_total_linha         = EXCLUDED.vl_total_linha,
       vl_frete_rateado       = EXCLUDED.vl_frete_rateado,
       vl_imposto_rateado     = EXCLUDED.vl_imposto_rateado,
       qt_dias_recebimento    = EXCLUDED.qt_dias_recebimento,
       qt_dias_atraso         = EXCLUDED.qt_dias_atraso,
       fl_recebimento_atrasado = EXCLUDED.fl_recebimento_atrasado,
       dt_modificacao_origem  = EXCLUDED.dt_modificacao_origem,
       dt_atualizacao         = CURRENT_TIMESTAMP
 WHERE f.dt_modificacao_origem <= EXCLUDED.dt_modificacao_origem
RETURNING (xmax = 0) AS inserido;
"""

FATOS = {
    "fato_vendas": FATO_VENDAS,
    "fato_compras": FATO_COMPRAS,
}
