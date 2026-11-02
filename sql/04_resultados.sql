-- =============================================================================
-- RESULTADOS CONSOLIDADOS DOS INDICADORES
--
-- Consultas que produzem os numeros citados no artigo, a partir das visoes do
-- esquema kpi. Execucao:
--   docker compose exec -T dw-postgres psql -U dw_user -d dw_adventureworks -f /sql/04_resultados.sql
-- =============================================================================

-- KPI 01: receita liquida por ano e por grupo de territorio.
SELECT nr_ano, SUM(qt_pedidos) AS qt_pedidos, SUM(vl_receita_liquida) AS vl_receita_liquida
  FROM kpi.mv_receita_liquida GROUP BY nr_ano ORDER BY nr_ano;

SELECT nm_grupo, SUM(vl_receita_liquida) AS vl_receita_liquida,
       ROUND(100.0 * SUM(vl_receita_liquida) / SUM(SUM(vl_receita_liquida)) OVER (), 2) AS pc_participacao
  FROM kpi.mv_receita_liquida GROUP BY nm_grupo ORDER BY vl_receita_liquida DESC;

-- KPI 02: ticket medio e mix por canal.
SELECT nm_canal, SUM(qt_pedidos) AS qt_pedidos, SUM(vl_receita_liquida) AS vl_receita_liquida,
       ROUND(SUM(vl_receita_liquida) / SUM(qt_pedidos), 2) AS vl_ticket_medio,
       ROUND(100.0 * SUM(vl_receita_liquida) / SUM(SUM(vl_receita_liquida)) OVER (), 2) AS pc_participacao
  FROM kpi.mv_ticket_medio GROUP BY nm_canal ORDER BY nm_canal;

SELECT nr_ano, nm_canal, vl_ticket_medio, pc_participacao_canal
  FROM kpi.mv_ticket_medio ORDER BY nr_ano, nm_canal;

-- KPI 03: margem bruta por ano e por categoria.
SELECT nr_ano, ROUND(100.0 * SUM(vl_margem_bruta) / SUM(vl_receita_liquida), 2) AS pc_margem_bruta
  FROM kpi.mv_margem_bruta GROUP BY nr_ano ORDER BY nr_ano;

SELECT nm_categoria, SUM(vl_receita_liquida) AS vl_receita_liquida,
       ROUND(100.0 * SUM(vl_margem_bruta) / SUM(vl_receita_liquida), 2) AS pc_margem_bruta
  FROM kpi.mv_margem_bruta GROUP BY nm_categoria ORDER BY vl_receita_liquida DESC;

SELECT nm_canal, SUM(vl_receita_liquida) AS vl_receita_liquida,
       SUM(vl_margem_bruta) AS vl_margem_bruta,
       ROUND(100.0 * SUM(vl_margem_bruta) / SUM(vl_receita_liquida), 2) AS pc_margem_bruta,
       ROUND(100.0 * SUM(vl_margem_bruta) / SUM(SUM(vl_margem_bruta)) OVER (), 2) AS pc_da_margem_total
  FROM kpi.mv_margem_bruta GROUP BY nm_canal ORDER BY nm_canal;

SELECT nr_ano, nm_canal,
       ROUND(100.0 * SUM(vl_margem_bruta) / SUM(vl_receita_liquida), 2) AS pc_margem_bruta
  FROM kpi.mv_margem_bruta GROUP BY nr_ano, nm_canal ORDER BY nr_ano, nm_canal;

-- KPI 04: taxa efetiva de desconto por tipo de promocao.
SELECT tp_promocao, SUM(vl_receita_bruta) AS vl_receita_bruta,
       SUM(vl_desconto_concedido) AS vl_desconto,
       ROUND(100.0 * SUM(vl_desconto_concedido) / SUM(vl_receita_bruta), 2) AS pc_desconto_efetivo
  FROM kpi.mv_taxa_desconto GROUP BY tp_promocao ORDER BY vl_desconto DESC;

-- KPI 05: crescimento YoY.
SELECT * FROM kpi.mv_crescimento_yoy ORDER BY nr_ano, nr_mes;

-- KPI 06: resumo da curva ABC.
SELECT ds_classe_abc, COUNT(*) AS qt_produtos,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pc_produtos,
       SUM(vl_receita_liquida) AS vl_receita,
       ROUND(100.0 * SUM(vl_receita_liquida) / SUM(SUM(vl_receita_liquida)) OVER (), 2) AS pc_receita
  FROM kpi.mv_curva_abc GROUP BY ds_classe_abc ORDER BY ds_classe_abc;

-- KPI 07: indice de sazonalidade por canal.
SELECT nr_mes, nm_mes,
       MAX(nr_indice_sazonal) FILTER (WHERE nm_canal = 'Internet') AS nr_indice_internet,
       MAX(nr_indice_sazonal) FILTER (WHERE nm_canal = 'Revenda')  AS nr_indice_revenda,
       MAX(nr_indice_sazonal) FILTER (WHERE nm_canal = 'Total')    AS nr_indice_total
  FROM kpi.mv_sazonalidade GROUP BY nr_mes, nm_mes ORDER BY nr_mes;

-- KPI 08: recompra por coorte.
SELECT * FROM kpi.mv_recompra ORDER BY nr_ano_coorte, tp_cliente;

-- KPI 09: tres maiores vendedores de cada ano.
SELECT * FROM kpi.mv_forca_vendas WHERE nr_ranking_ano <= 3 ORDER BY nr_ano, nr_ranking_ano;

-- KPI 10: fornecedores no periodo completo.
SELECT nm_fornecedor, SUM(qt_recebida) AS qt_recebida, SUM(qt_rejeitada) AS qt_rejeitada,
       SUM(vl_total_comprado) AS vl_total_comprado,
       ROUND(100.0 * SUM(qt_rejeitada) / NULLIF(SUM(qt_recebida), 0), 2) AS pc_taxa_rejeicao
  FROM kpi.mv_fornecedores
 GROUP BY nm_fornecedor
 ORDER BY pc_taxa_rejeicao DESC NULLS LAST, vl_total_comprado DESC
 LIMIT 8;

SELECT ROUND(100.0 * SUM(qt_rejeitada) / SUM(qt_recebida), 2) AS pc_taxa_rejeicao_geral,
       SUM(qt_rejeitada) AS qt_rejeitada,
       SUM(qt_rejeitada_ordem_recusada) AS qt_rejeitada_ordem_recusada,
       ROUND(100.0 * SUM(qt_rejeitada_ordem_recusada) / SUM(qt_rejeitada), 2) AS pc_em_ordem_recusada,
       SUM(vl_total_comprado) AS vl_total_comprado,
       COUNT(DISTINCT nm_fornecedor) AS qt_fornecedores_com_compra,
       COUNT(DISTINCT nm_fornecedor) FILTER (WHERE qt_rejeitada > 0) AS qt_com_rejeicao
  FROM kpi.mv_fornecedores;
