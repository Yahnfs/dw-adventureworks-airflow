-- =============================================================================
-- INDICADORES (KPIs) DO DATA WAREHOUSE ADVENTUREWORKS
--
-- Dez indicadores implementados exclusivamente sobre o modelo estrela, sem
-- nenhum acesso ao sistema transacional. Cada indicador e uma visao
-- materializada do esquema kpi, criada vazia (WITH NO DATA) e atualizada pela
-- DAG kpi_adventureworks sempre que o Data Warehouse muda.
--
-- Consulta: SELECT * FROM kpi.mv_<indicador>;
-- =============================================================================

-- #############################################################################
-- KPI 01 - RECEITA LIQUIDA
-- Formula   : SUM(vl_liquido), com vl_liquido = qt * preco * (1 - desconto)
-- Dimensoes : dim_tempo (ano, trimestre) x dim_territorio (grupo, territorio)
-- #############################################################################
CREATE MATERIALIZED VIEW IF NOT EXISTS kpi.mv_receita_liquida AS
SELECT t.nr_ano,
       t.ds_ano_trimestre,
       te.nm_grupo,
       te.nm_territorio,
       COUNT(DISTINCT f.id_pedido)  AS qt_pedidos,
       SUM(f.qt_vendida)            AS qt_itens,
       ROUND(SUM(f.vl_bruto), 2)    AS vl_receita_bruta,
       ROUND(SUM(f.vl_desconto), 2) AS vl_descontos,
       ROUND(SUM(f.vl_liquido), 2)  AS vl_receita_liquida
  FROM dw.fato_vendas    AS f
  JOIN dw.dim_tempo      AS t  ON t.sk_tempo = f.sk_tempo_pedido
  JOIN dw.dim_territorio AS te ON te.sk_territorio = f.sk_territorio
 GROUP BY t.nr_ano, t.ds_ano_trimestre, te.nm_grupo, te.nm_territorio
WITH NO DATA;

-- #############################################################################
-- KPI 02 - TICKET MEDIO E MIX POR CANAL
-- Formula   : SUM(vl_liquido) / COUNT(DISTINCT id_pedido)
--             participacao = receita do canal / receita do ano * 100
-- Dimensoes : dim_tempo (ano) x dim_canal_venda
-- Observacao: a contagem do pedido e distinta porque o grao do fato e o item.
-- #############################################################################
CREATE MATERIALIZED VIEW IF NOT EXISTS kpi.mv_ticket_medio AS
SELECT t.nr_ano,
       c.nm_canal,
       COUNT(DISTINCT f.id_pedido) AS qt_pedidos,
       ROUND(SUM(f.vl_liquido), 2) AS vl_receita_liquida,
       ROUND(SUM(f.vl_liquido) / NULLIF(COUNT(DISTINCT f.id_pedido), 0), 2)
                                   AS vl_ticket_medio,
       ROUND(SUM(f.qt_vendida)::numeric / NULLIF(COUNT(DISTINCT f.id_pedido), 0), 2)
                                   AS qt_itens_por_pedido,
       ROUND(100.0 * SUM(f.vl_liquido)
             / SUM(SUM(f.vl_liquido)) OVER (PARTITION BY t.nr_ano), 2)
                                   AS pc_participacao_canal
  FROM dw.fato_vendas     AS f
  JOIN dw.dim_tempo       AS t ON t.sk_tempo = f.sk_tempo_pedido
  JOIN dw.dim_canal_venda AS c ON c.sk_canal = f.sk_canal
 GROUP BY t.nr_ano, c.nm_canal
WITH NO DATA;

-- #############################################################################
-- KPI 03 - MARGEM BRUTA PERCENTUAL
-- Formula   : SUM(vl_margem_bruta) / SUM(vl_liquido) * 100
-- Dimensoes : dim_tempo (ano) x dim_canal_venda x dim_produto (categoria)
-- Observacao: o custo gravado no fato e o vigente na data do pedido
--             (ProductCostHistory), o que preserva a margem historica.
-- #############################################################################
CREATE MATERIALIZED VIEW IF NOT EXISTS kpi.mv_margem_bruta AS
SELECT t.nr_ano,
       c.nm_canal,
       p.nm_categoria,
       ROUND(SUM(f.vl_liquido), 2)      AS vl_receita_liquida,
       ROUND(SUM(f.vl_custo_total), 2)  AS vl_custo_total,
       ROUND(SUM(f.vl_margem_bruta), 2) AS vl_margem_bruta,
       ROUND(100.0 * SUM(f.vl_margem_bruta) / NULLIF(SUM(f.vl_liquido), 0), 2)
                                        AS pc_margem_bruta
  FROM dw.fato_vendas     AS f
  JOIN dw.dim_tempo       AS t ON t.sk_tempo = f.sk_tempo_pedido
  JOIN dw.dim_canal_venda AS c ON c.sk_canal = f.sk_canal
  JOIN dw.dim_produto     AS p ON p.sk_produto = f.sk_produto
 GROUP BY t.nr_ano, c.nm_canal, p.nm_categoria
WITH NO DATA;

-- #############################################################################
-- KPI 04 - TAXA EFETIVA DE DESCONTO
-- Formula   : SUM(vl_desconto) / SUM(vl_bruto) * 100
-- Dimensoes : dim_tempo (ano) x dim_promocao (tipo)
-- Observacao: razao de somas, e nao media de percentuais, para ponderar cada
--             linha pelo seu valor.
-- #############################################################################
CREATE MATERIALIZED VIEW IF NOT EXISTS kpi.mv_taxa_desconto AS
SELECT t.nr_ano,
       pr.tp_promocao,
       COUNT(*)                     AS qt_linhas_venda,
       SUM(f.qt_vendida)            AS qt_itens,
       ROUND(SUM(f.vl_bruto), 2)    AS vl_receita_bruta,
       ROUND(SUM(f.vl_desconto), 2) AS vl_desconto_concedido,
       ROUND(100.0 * SUM(f.vl_desconto) / NULLIF(SUM(f.vl_bruto), 0), 2)
                                    AS pc_desconto_efetivo
  FROM dw.fato_vendas  AS f
  JOIN dw.dim_tempo    AS t  ON t.sk_tempo = f.sk_tempo_pedido
  JOIN dw.dim_promocao AS pr ON pr.sk_promocao = f.sk_promocao
 GROUP BY t.nr_ano, pr.tp_promocao
WITH NO DATA;

-- #############################################################################
-- KPI 05 - CRESCIMENTO DE RECEITA ANO CONTRA ANO (YoY)
-- Formula   : (receita do mes - receita do mesmo mes no ano anterior)
--             / receita do mesmo mes no ano anterior * 100
-- Dimensoes : dim_tempo (ano, mes)
-- Tecnica   : LAG particionado pelo mes alinha cada mes ao seu equivalente.
-- #############################################################################
CREATE MATERIALIZED VIEW IF NOT EXISTS kpi.mv_crescimento_yoy AS
WITH receita_mensal AS (
    SELECT t.nr_ano, t.nr_mes, t.nm_mes, SUM(f.vl_liquido) AS vl_receita
      FROM dw.fato_vendas AS f
      JOIN dw.dim_tempo   AS t ON t.sk_tempo = f.sk_tempo_pedido
     WHERE t.sk_tempo > 0
     GROUP BY t.nr_ano, t.nr_mes, t.nm_mes
),
comparada AS (
    SELECT r.*,
           LAG(vl_receita) OVER (PARTITION BY nr_mes ORDER BY nr_ano) AS vl_anterior,
           LAG(nr_ano)     OVER (PARTITION BY nr_mes ORDER BY nr_ano) AS nr_ano_anterior
      FROM receita_mensal AS r
)
SELECT nr_ano,
       nr_mes,
       nm_mes,
       ROUND(vl_receita, 2)  AS vl_receita,
       ROUND(vl_anterior, 2) AS vl_receita_ano_anterior,
       ROUND(100.0 * (vl_receita - vl_anterior) / NULLIF(vl_anterior, 0), 2)
                             AS pc_crescimento_yoy
  FROM comparada
 WHERE nr_ano_anterior = nr_ano - 1
WITH NO DATA;

-- #############################################################################
-- KPI 06 - CURVA ABC DE PRODUTOS (PARETO)
-- Formula   : receita acumulada / receita total, no ranking decrescente.
--             Classe A ate 80% da receita, B ate 95%, C o restante.
-- Dimensoes : dim_produto (produto, categoria)
-- Padrao    : concentracao da receita em poucos itens.
-- #############################################################################
CREATE MATERIALIZED VIEW IF NOT EXISTS kpi.mv_curva_abc AS
WITH receita_produto AS (
    SELECT p.id_produto,
           p.nm_produto,
           p.nm_categoria,
           SUM(f.qt_vendida) AS qt_vendida,
           SUM(f.vl_liquido) AS vl_receita
      FROM dw.fato_vendas AS f
      JOIN dw.dim_produto AS p ON p.sk_produto = f.sk_produto
     GROUP BY p.id_produto, p.nm_produto, p.nm_categoria
),
acumulado AS (
    SELECT rp.*,
           ROW_NUMBER() OVER (ORDER BY vl_receita DESC) AS nr_ranking,
           100.0 * SUM(vl_receita) OVER (ORDER BY vl_receita DESC
                                         ROWS UNBOUNDED PRECEDING)
                 / SUM(vl_receita) OVER ()              AS pc_acumulado
      FROM receita_produto AS rp
)
SELECT nr_ranking,
       id_produto,
       nm_produto,
       nm_categoria,
       qt_vendida,
       ROUND(vl_receita, 2)   AS vl_receita_liquida,
       ROUND(pc_acumulado, 2) AS pc_acumulado,
       CASE WHEN pc_acumulado <= 80 THEN 'A'
            WHEN pc_acumulado <= 95 THEN 'B'
            ELSE 'C' END      AS ds_classe_abc
  FROM acumulado
WITH NO DATA;

-- #############################################################################
-- KPI 07 - INDICE DE SAZONALIDADE MENSAL
-- Formula   : receita do mes / receita media mensal do ano * 100,
--             em media sobre os anos completos (12 meses com venda).
-- Dimensoes : dim_tempo (mes) x dim_canal_venda
-- Padrao    : meses acima de 100 vendem mais que a media do proprio ano. A
--             razao e calculada dentro de cada ano para retirar o efeito do
--             crescimento entre anos; anos parciais ficam de fora. O corte por
--             canal importa porque os canais tem ciclos opostos, que se anulam
--             na linha 'Total'.
-- #############################################################################
CREATE MATERIALIZED VIEW IF NOT EXISTS kpi.mv_sazonalidade AS
WITH mensal AS (
    SELECT t.nr_ano, t.nr_mes, t.nm_mes,
           COALESCE(c.nm_canal, 'Total') AS nm_canal,
           SUM(f.vl_liquido)             AS vl_receita
      FROM dw.fato_vendas     AS f
      JOIN dw.dim_tempo       AS t ON t.sk_tempo = f.sk_tempo_pedido
      JOIN dw.dim_canal_venda AS c ON c.sk_canal = f.sk_canal
     WHERE t.sk_tempo > 0
     GROUP BY GROUPING SETS ((t.nr_ano, t.nr_mes, t.nm_mes, c.nm_canal),
                             (t.nr_ano, t.nr_mes, t.nm_mes))
),
anos_completos AS (
    SELECT nr_ano FROM mensal WHERE nm_canal = 'Total'
     GROUP BY nr_ano HAVING COUNT(*) = 12
),
razao AS (
    SELECT m.*,
           100.0 * m.vl_receita
                 / AVG(m.vl_receita) OVER (PARTITION BY m.nr_ano, m.nm_canal) AS nr_razao
      FROM mensal AS m
      JOIN anos_completos USING (nr_ano)
)
SELECT nm_canal,
       nr_mes,
       nm_mes,
       COUNT(*)                  AS qt_anos,
       ROUND(AVG(vl_receita), 2) AS vl_receita_media,
       ROUND(AVG(nr_razao), 2)   AS nr_indice_sazonal
  FROM razao
 GROUP BY nm_canal, nr_mes, nm_mes
WITH NO DATA;

-- #############################################################################
-- KPI 08 - TAXA DE RECOMPRA EM 180 DIAS, POR COORTE
-- Formula   : clientes que voltaram a comprar em ate 180 dias apos o primeiro
--             pedido / clientes da coorte * 100
-- Dimensoes : dim_tempo (ano do primeiro pedido) x dim_cliente (tipo)
-- Padrao    : comportamento de retencao por tipo de cliente. So entram
--             clientes cuja janela de 180 dias cabe no periodo observado,
--             para nao subestimar as coortes mais recentes.
-- #############################################################################
CREATE MATERIALIZED VIEW IF NOT EXISTS kpi.mv_recompra AS
WITH pedidos AS (
    SELECT f.sk_cliente, f.id_pedido, MIN(t.dt_data) AS dt_pedido
      FROM dw.fato_vendas AS f
      JOIN dw.dim_tempo   AS t ON t.sk_tempo = f.sk_tempo_pedido
     WHERE t.sk_tempo > 0
     GROUP BY f.sk_cliente, f.id_pedido
),
ordenados AS (
    SELECT p.*,
           ROW_NUMBER() OVER (PARTITION BY sk_cliente ORDER BY dt_pedido, id_pedido) AS nr_pedido,
           MIN(dt_pedido) OVER (PARTITION BY sk_cliente) AS dt_primeiro_pedido
      FROM pedidos AS p
),
clientes AS (
    SELECT sk_cliente,
           MIN(dt_primeiro_pedido) AS dt_primeiro_pedido,
           BOOL_OR(nr_pedido > 1 AND dt_pedido <= dt_primeiro_pedido + 180) AS fl_recomprou
      FROM ordenados
     GROUP BY sk_cliente
)
SELECT EXTRACT(YEAR FROM c.dt_primeiro_pedido)::int AS nr_ano_coorte,
       cl.tp_cliente,
       COUNT(*)                                     AS qt_clientes,
       COUNT(*) FILTER (WHERE c.fl_recomprou)       AS qt_recompraram,
       ROUND(100.0 * COUNT(*) FILTER (WHERE c.fl_recomprou) / COUNT(*), 2)
                                                    AS pc_recompra_180d
  FROM clientes AS c
  JOIN dw.dim_cliente AS cl ON cl.sk_cliente = c.sk_cliente
 WHERE c.dt_primeiro_pedido + 180 <= (SELECT MAX(dt_pedido) FROM pedidos)
 GROUP BY EXTRACT(YEAR FROM c.dt_primeiro_pedido), cl.tp_cliente
WITH NO DATA;

-- #############################################################################
-- KPI 09 - PRODUTIVIDADE DA FORCA DE VENDAS
-- Formula   : receita do vendedor no ano e participacao na receita do ano
--             atribuida a vendedores
-- Dimensoes : dim_funcionario (papel vendedor) x dim_tempo (ano)
-- Observacao: exclui o membro -1, que concentra as vendas pela internet.
-- #############################################################################
CREATE MATERIALIZED VIEW IF NOT EXISTS kpi.mv_forca_vendas AS
SELECT t.nr_ano,
       v.nm_funcionario,
       COUNT(DISTINCT f.id_pedido)      AS qt_pedidos,
       COUNT(DISTINCT f.sk_cliente)     AS qt_clientes_atendidos,
       ROUND(SUM(f.vl_liquido), 2)      AS vl_receita_liquida,
       ROUND(SUM(f.vl_margem_bruta), 2) AS vl_margem_bruta,
       ROUND(100.0 * SUM(f.vl_liquido)
             / SUM(SUM(f.vl_liquido)) OVER (PARTITION BY t.nr_ano), 2)
                                        AS pc_participacao_ano,
       RANK() OVER (PARTITION BY t.nr_ano ORDER BY SUM(f.vl_liquido) DESC)
                                        AS nr_ranking_ano
  FROM dw.fato_vendas     AS f
  JOIN dw.dim_tempo       AS t ON t.sk_tempo = f.sk_tempo_pedido
  JOIN dw.dim_funcionario AS v ON v.sk_funcionario = f.sk_vendedor
 WHERE f.sk_vendedor > 0
 GROUP BY t.nr_ano, v.nm_funcionario
WITH NO DATA;

-- #############################################################################
-- KPI 10 - TAXA DE REJEICAO E CUSTO POR FORNECEDOR
-- Formula   : SUM(qt_rejeitada) / SUM(qt_recebida) * 100
--             custo medio = valor comprado / quantidade pedida
-- Dimensoes : dim_fornecedor x dim_tempo (ano) x dim_status_pedido
-- Fato      : dw.fato_compras, segunda estrela do modelo, ligada a primeira
--             pelas dimensoes conformadas.
-- Observacao: ordens rejeitadas ficam fora do valor comprado, pois nao houve
--             compra, mas entram na taxa: sao remessas recusadas pela qualidade.
-- #############################################################################
CREATE MATERIALIZED VIEW IF NOT EXISTS kpi.mv_fornecedores AS
SELECT t.nr_ano,
       fo.nm_fornecedor,
       fo.ds_nivel_credito,
       COUNT(DISTINCT f.id_ordem_compra) AS qt_ordens_compra,
       SUM(f.qt_recebida)                AS qt_recebida,
       SUM(f.qt_rejeitada)               AS qt_rejeitada,
       COALESCE(SUM(f.qt_rejeitada) FILTER (WHERE s.fl_cancelado), 0)
                                         AS qt_rejeitada_ordem_recusada,
       ROUND(COALESCE(SUM(f.vl_total_linha) FILTER (WHERE NOT s.fl_cancelado), 0), 2)
                                         AS vl_total_comprado,
       ROUND(SUM(f.vl_total_linha) FILTER (WHERE NOT s.fl_cancelado)
             / NULLIF(SUM(f.qt_pedida) FILTER (WHERE NOT s.fl_cancelado), 0), 4)
                                         AS vl_custo_unitario_medio,
       ROUND(100.0 * SUM(f.qt_rejeitada) / NULLIF(SUM(f.qt_recebida), 0), 2)
                                         AS pc_taxa_rejeicao
  FROM dw.fato_compras      AS f
  JOIN dw.dim_tempo         AS t  ON t.sk_tempo = f.sk_tempo_pedido
  JOIN dw.dim_fornecedor    AS fo ON fo.sk_fornecedor = f.sk_fornecedor
  JOIN dw.dim_status_pedido AS s  ON s.sk_status = f.sk_status
 WHERE f.sk_fornecedor > 0
 GROUP BY t.nr_ano, fo.nm_fornecedor, fo.ds_nivel_credito
WITH NO DATA;
