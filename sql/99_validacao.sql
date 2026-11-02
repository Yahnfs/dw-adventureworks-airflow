-- =============================================================================
-- VALIDACAO E COMPROVACAO DA CARGA INCREMENTAL
--
-- Execucao:
--   docker compose exec -T dw-postgres psql -U dw_user -d dw_adventureworks -f /sql/99_validacao.sql
-- =============================================================================

-- 1. Volumetria das tabelas do modelo.
SELECT 'dw.dim_tempo'         AS tabela, count(*) AS qt_linhas FROM dw.dim_tempo
UNION ALL SELECT 'dw.dim_produto (todas as versoes)', count(*) FROM dw.dim_produto
UNION ALL SELECT 'dw.dim_produto (versao corrente)', count(*) FROM dw.dim_produto WHERE fl_corrente
UNION ALL SELECT 'dw.dim_cliente',       count(*) FROM dw.dim_cliente
UNION ALL SELECT 'dw.dim_funcionario',   count(*) FROM dw.dim_funcionario
UNION ALL SELECT 'dw.dim_territorio',    count(*) FROM dw.dim_territorio
UNION ALL SELECT 'dw.dim_geografia',     count(*) FROM dw.dim_geografia
UNION ALL SELECT 'dw.dim_fornecedor',    count(*) FROM dw.dim_fornecedor
UNION ALL SELECT 'dw.dim_promocao',      count(*) FROM dw.dim_promocao
UNION ALL SELECT 'dw.dim_metodo_envio',  count(*) FROM dw.dim_metodo_envio
UNION ALL SELECT 'dw.dim_canal_venda',   count(*) FROM dw.dim_canal_venda
UNION ALL SELECT 'dw.dim_status_pedido', count(*) FROM dw.dim_status_pedido
UNION ALL SELECT 'dw.fato_vendas',       count(*) FROM dw.fato_vendas
UNION ALL SELECT 'dw.fato_compras',      count(*) FROM dw.fato_compras
ORDER BY tabela;

-- 2. Topologia: nenhuma dimensao pode referenciar outra (condicao de estrela).
SELECT c.conrelid::regclass AS tabela_origem,
       c.confrelid::regclass AS tabela_referenciada,
       c.conname AS restricao
  FROM pg_constraint AS c
 WHERE c.contype = 'f'
   AND c.connamespace = 'dw'::regnamespace
   AND c.conrelid::regclass::text LIKE 'dw.dim_%';

-- 3. Comparativo entre os ciclos: volume e duracao por execucao da DAG.
SELECT id_lote,
       min(dt_inicio)                                                         AS inicio_ciclo,
       ROUND(EXTRACT(EPOCH FROM (max(dt_fim) - min(dt_inicio)))::numeric, 2)  AS segundos,
       sum(qt_extraidos)                                                      AS qt_extraidos,
       sum(qt_inseridos)                                                      AS qt_inseridos,
       sum(qt_atualizados)                                                    AS qt_atualizados,
       count(*) FILTER (WHERE ds_status = 'SEM_ALTERACAO')                    AS qt_entidades_sem_alteracao
  FROM meta.etl_execucao
 GROUP BY id_lote
 ORDER BY inicio_ciclo;

-- 4. Ultimo ciclo, entidade a entidade.
SELECT nm_entidade, ds_fase, ds_status, qt_extraidos, qt_inseridos, qt_atualizados,
       ds_marca_agua_de, ds_marca_agua_ate
  FROM meta.etl_execucao
 WHERE id_lote = (SELECT id_lote FROM meta.etl_execucao ORDER BY id_execucao DESC LIMIT 1)
 ORDER BY id_execucao;

-- 5. Conferencia origem x destino do ultimo ciclo.
SELECT ds_verificacao, vl_origem, vl_destino, fl_aprovado
  FROM meta.etl_validacao
 WHERE id_lote = (SELECT id_lote FROM meta.etl_validacao ORDER BY id_validacao DESC LIMIT 1)
 ORDER BY id_validacao;

-- 6. Efeitos de sql/98_simular_alteracoes.sql.
-- (A) SCD Tipo 2: duas versoes do produto 707, com vigencias adjacentes.
SELECT sk_produto, id_produto, nm_produto, vl_preco_lista, nr_versao,
       dt_inicio_validade, dt_fim_validade, fl_corrente
  FROM dw.dim_produto
 WHERE id_produto = 707
 ORDER BY nr_versao;

-- (B) SCD Tipo 1: uma unica linha, com dt_carga preservada.
SELECT sk_fornecedor, id_fornecedor, nm_fornecedor, nr_nivel_credito,
       ds_nivel_credito, dt_carga, dt_atualizacao
  FROM dw.dim_fornecedor
 WHERE id_fornecedor = 1492;

-- (C) Mudanca vista por tabela secundaria (Person.Person).
SELECT sk_cliente, id_cliente, nm_cliente, dt_carga, dt_atualizacao
  FROM dw.dim_cliente
 WHERE id_cliente = 11000;

-- (D) Alteracao so no cabecalho: as linhas do pedido foram atualizadas.
SELECT id_pedido, count(*) AS qt_linhas, min(qt_dias_entrega) AS qt_dias_entrega,
       min(dt_atualizacao) AS dt_atualizacao
  FROM dw.fato_vendas
 WHERE id_pedido = 43659
 GROUP BY id_pedido;

-- (E) e fidelidade historica: vendas antigas do produto 707 na versao 1 e a
--     venda nova na versao 2.
SELECT p.nr_versao, p.vl_preco_lista,
       count(*)       AS qt_linhas_venda,
       min(t.dt_data) AS primeira_venda,
       max(t.dt_data) AS ultima_venda
  FROM dw.fato_vendas AS f
  JOIN dw.dim_produto AS p ON p.sk_produto = f.sk_produto
  JOIN dw.dim_tempo   AS t ON t.sk_tempo = f.sk_tempo_pedido
 WHERE p.id_produto = 707
 GROUP BY p.nr_versao, p.vl_preco_lista
 ORDER BY p.nr_versao;
