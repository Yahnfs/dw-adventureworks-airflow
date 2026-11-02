-- =============================================================================
-- DATA WAREHOUSE ADVENTUREWORKS - DDL COMPLETO (PostgreSQL 16)
--
-- Modelo dimensional: Star Schema (Kimball) com duas tabelas fato
-- conectadas a dimensoes conformadas.
--
--   dw   -> camada dimensional (dimensoes + fatos) consumida pelas consultas OLAP
--   stg  -> area de staging (dados brutos extraidos do OLTP a cada ciclo de ETL)
--   meta -> metadados de controle da ETL incremental (marcas d'agua e log)
--   kpi  -> visoes materializadas dos indicadores (sql/03_kpis.sql)
--
-- Este script e idempotente: pode ser reexecutado sem efeitos colaterais.
-- Ele e montado automaticamente pelo docker-compose em
-- /docker-entrypoint-initdb.d, sendo executado na primeira subida do container.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS dw;
CREATE SCHEMA IF NOT EXISTS stg;
CREATE SCHEMA IF NOT EXISTS meta;
CREATE SCHEMA IF NOT EXISTS kpi;

COMMENT ON SCHEMA dw   IS 'Camada dimensional do Data Warehouse (star schema)';
COMMENT ON SCHEMA stg  IS 'Area de staging: recorte incremental extraido do OLTP';
COMMENT ON SCHEMA meta IS 'Metadados e controle de execucao da ETL incremental';
COMMENT ON SCHEMA kpi  IS 'Indicadores calculados sobre o modelo estrela';


-- =============================================================================
-- 1. CONTROLE DA ETL INCREMENTAL
-- =============================================================================

-- Armazena a marca d'agua (high-water mark) de cada entidade carregada.
-- A ETL le esta tabela antes de extrair e so busca no OLTP os registros com
-- ModifiedDate > dt_ultima_carga, tornando a carga incremental.
CREATE TABLE IF NOT EXISTS meta.etl_controle (
    nm_entidade          VARCHAR(60)  PRIMARY KEY,
    ds_tabela_origem     VARCHAR(120) NOT NULL,
    ds_coluna_controle   VARCHAR(60)  NOT NULL DEFAULT 'ModifiedDate',
    dt_ultima_carga      TIMESTAMP    NOT NULL DEFAULT '1900-01-01 00:00:00',
    qt_registros_ultima  BIGINT       NOT NULL DEFAULT 0,
    qt_registros_total   BIGINT       NOT NULL DEFAULT 0,
    dt_atualizacao       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE  meta.etl_controle                     IS 'Marca d''agua por entidade: base da estrategia de carga incremental';
COMMENT ON COLUMN meta.etl_controle.dt_ultima_carga     IS 'Maior ModifiedDate ja processado com sucesso para a entidade';
COMMENT ON COLUMN meta.etl_controle.qt_registros_ultima IS 'Volume de registros movimentados na ultima execucao';

-- Log de auditoria: uma linha por entidade por execucao da ETL.
CREATE TABLE IF NOT EXISTS meta.etl_execucao (
    id_execucao        BIGSERIAL PRIMARY KEY,
    id_lote            VARCHAR(250) NOT NULL,
    nm_entidade        VARCHAR(60)  NOT NULL,
    ds_fase            VARCHAR(20)  NOT NULL,
    dt_inicio          TIMESTAMP    NOT NULL,
    dt_fim             TIMESTAMP,
    qt_extraidos       BIGINT       DEFAULT 0,
    qt_inseridos       BIGINT       DEFAULT 0,
    qt_atualizados     BIGINT       DEFAULT 0,
    ds_marca_agua_de   TIMESTAMP,
    ds_marca_agua_ate  TIMESTAMP,
    ds_status          VARCHAR(20)  NOT NULL DEFAULT 'EM_EXECUCAO',
    ds_mensagem        TEXT
);

CREATE INDEX IF NOT EXISTS ix_etl_execucao_lote ON meta.etl_execucao (id_lote);

COMMENT ON TABLE  meta.etl_execucao         IS 'Log de auditoria das execucoes da ETL (rastreabilidade e reprocessamento)';
COMMENT ON COLUMN meta.etl_execucao.id_lote IS 'run_id do Airflow: liga cada linha de log a execucao da DAG';

-- Resultado das verificacoes de consistencia feitas ao final de cada ciclo.
CREATE TABLE IF NOT EXISTS meta.etl_validacao (
    id_validacao    BIGSERIAL PRIMARY KEY,
    id_lote         VARCHAR(250)  NOT NULL,
    ds_verificacao  VARCHAR(120)  NOT NULL,
    vl_origem       NUMERIC(19,4),
    vl_destino      NUMERIC(19,4),
    fl_aprovado     BOOLEAN       NOT NULL,
    dt_verificacao  TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_etl_validacao_lote ON meta.etl_validacao (id_lote);

COMMENT ON TABLE  meta.etl_validacao                IS 'Conferencia OLTP x DW e testes de integridade de cada ciclo de ETL';
COMMENT ON COLUMN meta.etl_validacao.id_lote        IS 'run_id do Airflow que executou a verificacao';
COMMENT ON COLUMN meta.etl_validacao.ds_verificacao IS 'Descricao da verificacao realizada';
COMMENT ON COLUMN meta.etl_validacao.vl_origem      IS 'Valor apurado no OLTP ou valor esperado';
COMMENT ON COLUMN meta.etl_validacao.vl_destino     IS 'Valor apurado no Data Warehouse';
COMMENT ON COLUMN meta.etl_validacao.fl_aprovado    IS 'TRUE quando a verificacao foi aprovada';
COMMENT ON COLUMN meta.etl_validacao.dt_verificacao IS 'Momento da verificacao';


-- =============================================================================
-- 2. DIMENSOES
--
-- Convencoes adotadas:
--   * sk_*  = surrogate key (chave substituta, inteira, gerada pelo DW)
--   * id_*  = chave natural herdada do sistema de origem (OLTP)
--   * Toda dimensao possui o membro "Nao Informado" com sk = -1, usado quando
--     a chave estrangeira do fato e nula ou nao encontrada (late arriving).
--   * hash_scd = digest MD5 dos atributos, usado para detectar alteracao real
--     de conteudo sem comparar coluna a coluna.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 2.1 dim_tempo - dimensao de calendario, gerada proceduralmente pela ETL.
--     A SK e inteligente no formato AAAAMMDD, o que dispensa lookup na carga
--     dos fatos e torna as consultas por periodo legiveis.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.dim_tempo (
    sk_tempo            INTEGER      PRIMARY KEY,
    dt_data             DATE         NOT NULL UNIQUE,
    nr_ano              SMALLINT     NOT NULL,
    nr_semestre         SMALLINT     NOT NULL,
    nr_trimestre        SMALLINT     NOT NULL,
    nr_mes              SMALLINT     NOT NULL,
    nr_dia              SMALLINT     NOT NULL,
    nr_semana_ano       SMALLINT     NOT NULL,
    nr_dia_semana       SMALLINT     NOT NULL,
    nr_dia_ano          SMALLINT     NOT NULL,
    nm_mes              VARCHAR(15)  NOT NULL,
    nm_mes_abrev        VARCHAR(3)   NOT NULL,
    nm_dia_semana       VARCHAR(15)  NOT NULL,
    ds_ano_mes          CHAR(7)      NOT NULL,
    ds_ano_trimestre    CHAR(7)      NOT NULL,
    fl_fim_semana       BOOLEAN      NOT NULL,
    dt_primeiro_dia_mes DATE         NOT NULL,
    dt_ultimo_dia_mes   DATE         NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_dim_tempo_ano_mes ON dw.dim_tempo (nr_ano, nr_mes);

COMMENT ON TABLE  dw.dim_tempo         IS 'Dimensao calendario diaria; SK inteligente no formato AAAAMMDD';
COMMENT ON COLUMN dw.dim_tempo.sk_tempo IS 'Chave substituta no formato AAAAMMDD (ex.: 20130715). -1 = Nao Informado';

-- -----------------------------------------------------------------------------
-- 2.2 dim_produto - SCD Tipo 2.
--     Preserva o historico de alteracoes de preco de lista, custo padrao e
--     hierarquia de categoria. Cada versao vigente em um intervalo de datas.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.dim_produto (
    sk_produto             BIGSERIAL     PRIMARY KEY,
    id_produto             INTEGER       NOT NULL,
    cd_produto             VARCHAR(25),
    nm_produto             VARCHAR(100)  NOT NULL,
    nm_categoria           VARCHAR(60)   NOT NULL DEFAULT 'Sem Categoria',
    nm_subcategoria        VARCHAR(60)   NOT NULL DEFAULT 'Sem Subcategoria',
    nm_modelo              VARCHAR(60)   NOT NULL DEFAULT 'Sem Modelo',
    ds_linha               VARCHAR(30)   NOT NULL DEFAULT 'Nao Informado',
    ds_classe              VARCHAR(30)   NOT NULL DEFAULT 'Nao Informado',
    ds_estilo              VARCHAR(30)   NOT NULL DEFAULT 'Nao Informado',
    ds_cor                 VARCHAR(30)   NOT NULL DEFAULT 'Nao Informado',
    ds_tamanho             VARCHAR(15),
    vl_peso                NUMERIC(12,2),
    nm_unidade_peso        VARCHAR(30),
    vl_custo_padrao        NUMERIC(19,4) NOT NULL DEFAULT 0,
    vl_preco_lista         NUMERIC(19,4) NOT NULL DEFAULT 0,
    fl_fabricacao_propria  BOOLEAN       NOT NULL DEFAULT FALSE,
    fl_produto_acabado     BOOLEAN       NOT NULL DEFAULT FALSE,
    qt_estoque_seguranca   INTEGER,
    qt_ponto_reposicao     INTEGER,
    nr_dias_fabricacao     INTEGER,
    dt_inicio_venda        DATE,
    dt_fim_venda           DATE,
    dt_descontinuado       DATE,
    -- Controle SCD Tipo 2
    nr_versao              INTEGER       NOT NULL DEFAULT 1,
    dt_inicio_validade     DATE          NOT NULL DEFAULT DATE '1900-01-01',
    dt_fim_validade        DATE          NOT NULL DEFAULT DATE '9999-12-31',
    fl_corrente            BOOLEAN       NOT NULL DEFAULT TRUE,
    hash_scd               CHAR(32)      NOT NULL,
    -- Auditoria
    dt_modificacao_origem  TIMESTAMP,
    dt_carga               TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    dt_atualizacao         TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Garante uma unica versao vigente por produto (regra central do SCD Tipo 2).
CREATE UNIQUE INDEX IF NOT EXISTS ux_dim_produto_corrente
    ON dw.dim_produto (id_produto) WHERE fl_corrente;
CREATE INDEX IF NOT EXISTS ix_dim_produto_natural
    ON dw.dim_produto (id_produto, dt_inicio_validade, dt_fim_validade);
CREATE INDEX IF NOT EXISTS ix_dim_produto_categoria
    ON dw.dim_produto (nm_categoria, nm_subcategoria);

COMMENT ON TABLE  dw.dim_produto                    IS 'Dimensao produto com historico (SCD Tipo 2); hierarquia Categoria > Subcategoria > Modelo > Produto';
COMMENT ON COLUMN dw.dim_produto.fl_corrente        IS 'TRUE apenas na versao vigente do produto';
COMMENT ON COLUMN dw.dim_produto.hash_scd           IS 'MD5 dos atributos monitorados; alteracao no hash dispara nova versao';

-- -----------------------------------------------------------------------------
-- 2.3 dim_cliente - SCD Tipo 1 (sobrescrita).
--     Unifica pessoa fisica (consumidor final) e loja (revendedor).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.dim_cliente (
    sk_cliente            BIGSERIAL     PRIMARY KEY,
    id_cliente            INTEGER       NOT NULL UNIQUE,
    cd_conta              VARCHAR(15),
    tp_cliente            VARCHAR(20)   NOT NULL DEFAULT 'Nao Informado',
    nm_cliente            VARCHAR(150)  NOT NULL,
    nm_primeiro           VARCHAR(60),
    nm_sobrenome          VARCHAR(60),
    nm_loja               VARCHAR(60),
    ds_email              VARCHAR(80),
    fl_aceita_promocao    BOOLEAN       NOT NULL DEFAULT FALSE,
    hash_scd              CHAR(32)      NOT NULL,
    dt_modificacao_origem TIMESTAMP,
    dt_carga              TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    dt_atualizacao        TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE  dw.dim_cliente            IS 'Dimensao cliente (SCD Tipo 1), unificando pessoa fisica e loja revendedora';
COMMENT ON COLUMN dw.dim_cliente.tp_cliente IS 'Pessoa Fisica | Loja - segmenta os canais Internet e Revenda';

-- -----------------------------------------------------------------------------
-- 2.4 dim_funcionario - SCD Tipo 1, dimensao de multiplos papeis
--     (role-playing): atua como VENDEDOR na fato_vendas e como COMPRADOR
--     na fato_compras.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.dim_funcionario (
    sk_funcionario        BIGSERIAL     PRIMARY KEY,
    id_funcionario        INTEGER       NOT NULL UNIQUE,
    nm_funcionario        VARCHAR(150)  NOT NULL,
    ds_cargo              VARCHAR(60),
    ds_genero             VARCHAR(20),
    ds_estado_civil       VARCHAR(20),
    dt_nascimento         DATE,
    dt_admissao           DATE,
    fl_assalariado        BOOLEAN,
    fl_vendedor           BOOLEAN       NOT NULL DEFAULT FALSE,
    vl_cota_vendas        NUMERIC(19,4),
    vl_bonus              NUMERIC(19,4),
    pc_comissao           NUMERIC(10,4),
    hash_scd              CHAR(32)      NOT NULL,
    dt_modificacao_origem TIMESTAMP,
    dt_carga              TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    dt_atualizacao        TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE dw.dim_funcionario IS 'Dimensao funcionario (SCD Tipo 1) de multiplos papeis: vendedor em fato_vendas e comprador em fato_compras';

-- -----------------------------------------------------------------------------
-- 2.5 dim_territorio - territorio comercial (hierarquia Grupo > Pais > Territorio)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.dim_territorio (
    sk_territorio         BIGSERIAL     PRIMARY KEY,
    id_territorio         INTEGER       NOT NULL UNIQUE,
    nm_territorio         VARCHAR(60)   NOT NULL,
    nm_grupo              VARCHAR(60)   NOT NULL DEFAULT 'Nao Informado',
    cd_pais               CHAR(3),
    nm_pais               VARCHAR(60),
    vl_vendas_ano_atual   NUMERIC(19,4),
    vl_vendas_ano_ante    NUMERIC(19,4),
    vl_custo_ano_atual    NUMERIC(19,4),
    hash_scd              CHAR(32)      NOT NULL,
    dt_modificacao_origem TIMESTAMP,
    dt_carga              TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    dt_atualizacao        TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE dw.dim_territorio IS 'Dimensao territorio de vendas; hierarquia Grupo (continente) > Pais > Territorio';

-- -----------------------------------------------------------------------------
-- 2.6 dim_geografia - localizacao do endereco de entrega
--     (hierarquia Pais > Estado/Provincia > Cidade)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.dim_geografia (
    sk_geografia          BIGSERIAL     PRIMARY KEY,
    id_endereco           INTEGER       NOT NULL UNIQUE,
    ds_cidade             VARCHAR(60)   NOT NULL DEFAULT 'Nao Informado',
    cd_estado             VARCHAR(5),
    nm_estado             VARCHAR(60)   NOT NULL DEFAULT 'Nao Informado',
    cd_pais               CHAR(3),
    nm_pais               VARCHAR(60)   NOT NULL DEFAULT 'Nao Informado',
    nm_regiao             VARCHAR(60)   NOT NULL DEFAULT 'Nao Informado',
    cd_postal             VARCHAR(15),
    hash_scd              CHAR(32)      NOT NULL,
    dt_modificacao_origem TIMESTAMP,
    dt_carga              TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    dt_atualizacao        TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_dim_geografia_pais ON dw.dim_geografia (nm_pais, nm_estado);

COMMENT ON TABLE dw.dim_geografia IS 'Dimensao geografica do endereco de entrega; hierarquia Regiao > Pais > Estado > Cidade';

-- -----------------------------------------------------------------------------
-- 2.7 dim_fornecedor
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.dim_fornecedor (
    sk_fornecedor         BIGSERIAL     PRIMARY KEY,
    id_fornecedor         INTEGER       NOT NULL UNIQUE,
    cd_conta              VARCHAR(15),
    nm_fornecedor         VARCHAR(60)   NOT NULL,
    nr_nivel_credito      SMALLINT,
    ds_nivel_credito      VARCHAR(20),
    fl_fornecedor_ativo   BOOLEAN       NOT NULL DEFAULT TRUE,
    fl_preferencial       BOOLEAN       NOT NULL DEFAULT FALSE,
    hash_scd              CHAR(32)      NOT NULL,
    dt_modificacao_origem TIMESTAMP,
    dt_carga              TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    dt_atualizacao        TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE dw.dim_fornecedor IS 'Dimensao fornecedor, utilizada pela fato_compras';

-- -----------------------------------------------------------------------------
-- 2.8 dim_promocao - ofertas e descontos aplicados ao item de venda
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.dim_promocao (
    sk_promocao           BIGSERIAL     PRIMARY KEY,
    id_promocao           INTEGER       NOT NULL UNIQUE,
    ds_promocao           VARCHAR(255)  NOT NULL,
    tp_promocao           VARCHAR(60)   NOT NULL DEFAULT 'Nao Informado',
    ds_categoria          VARCHAR(60)   NOT NULL DEFAULT 'Nao Informado',
    pc_desconto           NUMERIC(10,4) NOT NULL DEFAULT 0,
    qt_minima             INTEGER,
    qt_maxima             INTEGER,
    dt_inicio             DATE,
    dt_fim                DATE,
    fl_com_desconto       BOOLEAN       NOT NULL DEFAULT FALSE,
    hash_scd              CHAR(32)      NOT NULL,
    dt_modificacao_origem TIMESTAMP,
    dt_carga              TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    dt_atualizacao        TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON COLUMN dw.dim_promocao.fl_com_desconto IS 'FALSE para a oferta neutra "No Discount" (id 1), TRUE para promocoes efetivas';

-- -----------------------------------------------------------------------------
-- 2.9 dim_metodo_envio - transportadora / modalidade de frete
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.dim_metodo_envio (
    sk_metodo_envio       BIGSERIAL     PRIMARY KEY,
    id_metodo_envio       INTEGER       NOT NULL UNIQUE,
    nm_metodo_envio       VARCHAR(60)   NOT NULL,
    vl_taxa_base          NUMERIC(19,4),
    vl_taxa_por_peso      NUMERIC(19,4),
    hash_scd              CHAR(32)      NOT NULL,
    dt_modificacao_origem TIMESTAMP,
    dt_carga              TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    dt_atualizacao        TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------------------------
-- 2.10 dim_canal_venda - dimensao estatica (junk dimension de canal)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.dim_canal_venda (
    sk_canal    INTEGER      PRIMARY KEY,
    cd_canal    VARCHAR(15)  NOT NULL,
    nm_canal    VARCHAR(60)  NOT NULL,
    ds_canal    VARCHAR(255)
);

-- -----------------------------------------------------------------------------
-- 2.11 dim_status_pedido - dimensao estatica compartilhada por vendas e compras
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.dim_status_pedido (
    sk_status    INTEGER      PRIMARY KEY,
    cd_status    SMALLINT     NOT NULL,
    ds_dominio   VARCHAR(10)  NOT NULL,
    nm_status    VARCHAR(40)  NOT NULL,
    fl_concluido BOOLEAN      NOT NULL DEFAULT FALSE,
    fl_cancelado BOOLEAN      NOT NULL DEFAULT FALSE,
    UNIQUE (ds_dominio, cd_status)
);

COMMENT ON COLUMN dw.dim_status_pedido.ds_dominio IS 'VENDA ou COMPRA - o mesmo codigo numerico tem significados distintos em cada processo';


-- =============================================================================
-- 3. TABELAS FATO
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 3.1 fato_vendas
--     Grao: uma linha por ITEM de pedido de venda (Sales.SalesOrderDetail).
--     Tipo: fato transacional, aditiva (exceto percentuais).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.fato_vendas (
    sk_fato_vendas          BIGSERIAL     PRIMARY KEY,

    -- Chaves estrangeiras para as dimensoes
    sk_tempo_pedido         INTEGER       NOT NULL,
    sk_tempo_vencimento     INTEGER       NOT NULL,
    sk_tempo_envio          INTEGER       NOT NULL,
    sk_produto              BIGINT        NOT NULL,
    sk_cliente              BIGINT        NOT NULL,
    sk_vendedor             BIGINT        NOT NULL,
    sk_territorio           BIGINT        NOT NULL,
    sk_promocao             BIGINT        NOT NULL,
    sk_geografia_entrega    BIGINT        NOT NULL,
    sk_metodo_envio         BIGINT        NOT NULL,
    sk_canal                INTEGER       NOT NULL,
    sk_status               INTEGER       NOT NULL,

    -- Dimensoes degeneradas (identificadores da transacao)
    id_item_venda           INTEGER       NOT NULL UNIQUE,
    id_pedido               INTEGER       NOT NULL,
    nr_pedido               VARCHAR(25)   NOT NULL,
    nr_pedido_cliente       VARCHAR(25),

    -- Metricas
    qt_vendida              INTEGER       NOT NULL,
    vl_preco_unitario       NUMERIC(19,4) NOT NULL,
    pc_desconto_unitario    NUMERIC(10,4) NOT NULL DEFAULT 0,
    vl_bruto                NUMERIC(19,4) NOT NULL,
    vl_desconto             NUMERIC(19,4) NOT NULL DEFAULT 0,
    vl_liquido              NUMERIC(19,4) NOT NULL,
    vl_custo_unitario       NUMERIC(19,4) NOT NULL DEFAULT 0,
    vl_custo_total          NUMERIC(19,4) NOT NULL DEFAULT 0,
    vl_margem_bruta         NUMERIC(19,4) NOT NULL DEFAULT 0,
    vl_frete_rateado        NUMERIC(19,4) NOT NULL DEFAULT 0,
    vl_imposto_rateado      NUMERIC(19,4) NOT NULL DEFAULT 0,
    qt_dias_entrega         INTEGER,
    qt_dias_atraso          INTEGER,
    fl_entrega_atrasada     BOOLEAN       NOT NULL DEFAULT FALSE,
    fl_pedido_online        BOOLEAN       NOT NULL DEFAULT FALSE,

    -- Auditoria
    dt_modificacao_origem   TIMESTAMP     NOT NULL,
    dt_carga                TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    dt_atualizacao          TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_fv_tempo_pedido     FOREIGN KEY (sk_tempo_pedido)      REFERENCES dw.dim_tempo (sk_tempo),
    CONSTRAINT fk_fv_tempo_vencimento FOREIGN KEY (sk_tempo_vencimento)  REFERENCES dw.dim_tempo (sk_tempo),
    CONSTRAINT fk_fv_tempo_envio      FOREIGN KEY (sk_tempo_envio)       REFERENCES dw.dim_tempo (sk_tempo),
    CONSTRAINT fk_fv_produto          FOREIGN KEY (sk_produto)           REFERENCES dw.dim_produto (sk_produto),
    CONSTRAINT fk_fv_cliente          FOREIGN KEY (sk_cliente)           REFERENCES dw.dim_cliente (sk_cliente),
    CONSTRAINT fk_fv_vendedor         FOREIGN KEY (sk_vendedor)          REFERENCES dw.dim_funcionario (sk_funcionario),
    CONSTRAINT fk_fv_territorio       FOREIGN KEY (sk_territorio)        REFERENCES dw.dim_territorio (sk_territorio),
    CONSTRAINT fk_fv_promocao         FOREIGN KEY (sk_promocao)          REFERENCES dw.dim_promocao (sk_promocao),
    CONSTRAINT fk_fv_geografia        FOREIGN KEY (sk_geografia_entrega) REFERENCES dw.dim_geografia (sk_geografia),
    CONSTRAINT fk_fv_metodo_envio     FOREIGN KEY (sk_metodo_envio)      REFERENCES dw.dim_metodo_envio (sk_metodo_envio),
    CONSTRAINT fk_fv_canal            FOREIGN KEY (sk_canal)             REFERENCES dw.dim_canal_venda (sk_canal),
    CONSTRAINT fk_fv_status           FOREIGN KEY (sk_status)            REFERENCES dw.dim_status_pedido (sk_status)
);

CREATE INDEX IF NOT EXISTS ix_fv_tempo      ON dw.fato_vendas (sk_tempo_pedido);
CREATE INDEX IF NOT EXISTS ix_fv_produto    ON dw.fato_vendas (sk_produto);
CREATE INDEX IF NOT EXISTS ix_fv_cliente    ON dw.fato_vendas (sk_cliente);
CREATE INDEX IF NOT EXISTS ix_fv_territorio ON dw.fato_vendas (sk_territorio);
CREATE INDEX IF NOT EXISTS ix_fv_vendedor   ON dw.fato_vendas (sk_vendedor);
CREATE INDEX IF NOT EXISTS ix_fv_pedido     ON dw.fato_vendas (id_pedido);

COMMENT ON TABLE  dw.fato_vendas                     IS 'Fato transacional de vendas; grao = item de pedido (Sales.SalesOrderDetail)';
COMMENT ON COLUMN dw.fato_vendas.id_item_venda       IS 'Dimensao degenerada e chave de negocio usada no MERGE incremental';
COMMENT ON COLUMN dw.fato_vendas.vl_bruto            IS 'qt_vendida * vl_preco_unitario (antes do desconto)';
COMMENT ON COLUMN dw.fato_vendas.vl_liquido          IS 'Receita liquida da linha: vl_bruto - vl_desconto';
COMMENT ON COLUMN dw.fato_vendas.vl_margem_bruta     IS 'vl_liquido - vl_custo_total';
COMMENT ON COLUMN dw.fato_vendas.vl_frete_rateado    IS 'Frete do cabecalho do pedido rateado pela participacao da linha na receita';

-- -----------------------------------------------------------------------------
-- 3.2 fato_compras
--     Grao: uma linha por ITEM de ordem de compra (Purchasing.PurchaseOrderDetail).
--     Tipo: fato transacional, aditiva.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.fato_compras (
    sk_fato_compras         BIGSERIAL     PRIMARY KEY,

    sk_tempo_pedido         INTEGER       NOT NULL,
    sk_tempo_previsto       INTEGER       NOT NULL,
    sk_tempo_recebimento    INTEGER       NOT NULL,
    sk_produto              BIGINT        NOT NULL,
    sk_fornecedor           BIGINT        NOT NULL,
    sk_comprador            BIGINT        NOT NULL,
    sk_metodo_envio         BIGINT        NOT NULL,
    sk_status               INTEGER       NOT NULL,

    id_item_compra          INTEGER       NOT NULL UNIQUE,
    id_ordem_compra         INTEGER       NOT NULL,

    qt_pedida               INTEGER       NOT NULL,
    qt_recebida             NUMERIC(12,2) NOT NULL DEFAULT 0,
    qt_rejeitada            NUMERIC(12,2) NOT NULL DEFAULT 0,
    qt_aceita               NUMERIC(12,2) NOT NULL DEFAULT 0,
    vl_preco_unitario       NUMERIC(19,4) NOT NULL,
    vl_total_linha          NUMERIC(19,4) NOT NULL,
    vl_frete_rateado        NUMERIC(19,4) NOT NULL DEFAULT 0,
    vl_imposto_rateado      NUMERIC(19,4) NOT NULL DEFAULT 0,
    qt_dias_recebimento     INTEGER,
    qt_dias_atraso          INTEGER,
    fl_recebimento_atrasado BOOLEAN       NOT NULL DEFAULT FALSE,

    dt_modificacao_origem   TIMESTAMP     NOT NULL,
    dt_carga                TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    dt_atualizacao          TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_fc_tempo_pedido   FOREIGN KEY (sk_tempo_pedido)      REFERENCES dw.dim_tempo (sk_tempo),
    CONSTRAINT fk_fc_tempo_previsto FOREIGN KEY (sk_tempo_previsto)    REFERENCES dw.dim_tempo (sk_tempo),
    CONSTRAINT fk_fc_tempo_receb    FOREIGN KEY (sk_tempo_recebimento) REFERENCES dw.dim_tempo (sk_tempo),
    CONSTRAINT fk_fc_produto        FOREIGN KEY (sk_produto)           REFERENCES dw.dim_produto (sk_produto),
    CONSTRAINT fk_fc_fornecedor     FOREIGN KEY (sk_fornecedor)        REFERENCES dw.dim_fornecedor (sk_fornecedor),
    CONSTRAINT fk_fc_comprador      FOREIGN KEY (sk_comprador)         REFERENCES dw.dim_funcionario (sk_funcionario),
    CONSTRAINT fk_fc_metodo_envio   FOREIGN KEY (sk_metodo_envio)      REFERENCES dw.dim_metodo_envio (sk_metodo_envio),
    CONSTRAINT fk_fc_status         FOREIGN KEY (sk_status)            REFERENCES dw.dim_status_pedido (sk_status)
);

CREATE INDEX IF NOT EXISTS ix_fc_tempo      ON dw.fato_compras (sk_tempo_pedido);
CREATE INDEX IF NOT EXISTS ix_fc_produto    ON dw.fato_compras (sk_produto);
CREATE INDEX IF NOT EXISTS ix_fc_fornecedor ON dw.fato_compras (sk_fornecedor);

COMMENT ON TABLE  dw.fato_compras              IS 'Fato transacional de compras; grao = item de ordem de compra (Purchasing.PurchaseOrderDetail)';
COMMENT ON COLUMN dw.fato_compras.qt_aceita    IS 'qt_recebida - qt_rejeitada';
COMMENT ON COLUMN dw.fato_compras.sk_comprador IS 'Papel de COMPRADOR da dimensao conformada dw.dim_funcionario';


-- =============================================================================
-- 4. MEMBROS "NAO INFORMADO" (SK = -1)
--
-- Evitam chaves estrangeiras nulas nos fatos. Toda linha de fato cuja chave
-- natural seja nula ou nao encontrada na dimensao aponta para o membro -1,
-- preservando a integridade referencial e a contagem correta de registros.
-- =============================================================================

INSERT INTO dw.dim_tempo (
    sk_tempo, dt_data, nr_ano, nr_semestre, nr_trimestre, nr_mes, nr_dia,
    nr_semana_ano, nr_dia_semana, nr_dia_ano, nm_mes, nm_mes_abrev,
    nm_dia_semana, ds_ano_mes, ds_ano_trimestre, fl_fim_semana,
    dt_primeiro_dia_mes, dt_ultimo_dia_mes)
VALUES (-1, DATE '1900-01-01', 1900, 1, 1, 1, 1, 1, 1, 1,
        'Nao Informado', 'N/I', 'Nao Informado', '1900-01', '1900-Q1', FALSE,
        DATE '1900-01-01', DATE '1900-01-31')
ON CONFLICT (sk_tempo) DO NOTHING;

INSERT INTO dw.dim_produto (sk_produto, id_produto, nm_produto, hash_scd)
VALUES (-1, -1, 'Nao Informado', md5('NAO_INFORMADO'))
ON CONFLICT (sk_produto) DO NOTHING;

INSERT INTO dw.dim_cliente (sk_cliente, id_cliente, nm_cliente, hash_scd)
VALUES (-1, -1, 'Nao Informado', md5('NAO_INFORMADO'))
ON CONFLICT (sk_cliente) DO NOTHING;

INSERT INTO dw.dim_funcionario (sk_funcionario, id_funcionario, nm_funcionario, hash_scd)
VALUES (-1, -1, 'Nao Informado', md5('NAO_INFORMADO'))
ON CONFLICT (sk_funcionario) DO NOTHING;

INSERT INTO dw.dim_territorio (sk_territorio, id_territorio, nm_territorio, hash_scd)
VALUES (-1, -1, 'Nao Informado', md5('NAO_INFORMADO'))
ON CONFLICT (sk_territorio) DO NOTHING;

INSERT INTO dw.dim_geografia (sk_geografia, id_endereco, hash_scd)
VALUES (-1, -1, md5('NAO_INFORMADO'))
ON CONFLICT (sk_geografia) DO NOTHING;

INSERT INTO dw.dim_fornecedor (sk_fornecedor, id_fornecedor, nm_fornecedor, hash_scd)
VALUES (-1, -1, 'Nao Informado', md5('NAO_INFORMADO'))
ON CONFLICT (sk_fornecedor) DO NOTHING;

INSERT INTO dw.dim_promocao (sk_promocao, id_promocao, ds_promocao, hash_scd)
VALUES (-1, -1, 'Nao Informado', md5('NAO_INFORMADO'))
ON CONFLICT (sk_promocao) DO NOTHING;

INSERT INTO dw.dim_metodo_envio (sk_metodo_envio, id_metodo_envio, nm_metodo_envio, hash_scd)
VALUES (-1, -1, 'Nao Informado', md5('NAO_INFORMADO'))
ON CONFLICT (sk_metodo_envio) DO NOTHING;


-- =============================================================================
-- 5. CARGA DAS DIMENSOES ESTATICAS
-- =============================================================================

INSERT INTO dw.dim_canal_venda (sk_canal, cd_canal, nm_canal, ds_canal) VALUES
    (-1, 'N/I',      'Nao Informado', 'Canal nao identificado'),
    ( 1, 'ONLINE',   'Internet',      'Pedido realizado diretamente pelo cliente no site (OnlineOrderFlag = 1)'),
    ( 2, 'REVENDA',  'Revenda',       'Pedido intermediado por vendedor junto a loja revendedora (OnlineOrderFlag = 0)')
ON CONFLICT (sk_canal) DO NOTHING;

INSERT INTO dw.dim_status_pedido (sk_status, cd_status, ds_dominio, nm_status, fl_concluido, fl_cancelado) VALUES
    (-1, -1, 'N/I',   'Nao Informado',   FALSE, FALSE),
    ( 1,  1, 'VENDA', 'Em Andamento',    FALSE, FALSE),
    ( 2,  2, 'VENDA', 'Aprovado',        FALSE, FALSE),
    ( 3,  3, 'VENDA', 'Pendente',        FALSE, FALSE),
    ( 4,  4, 'VENDA', 'Rejeitado',       FALSE, TRUE),
    ( 5,  5, 'VENDA', 'Enviado',         TRUE,  FALSE),
    ( 6,  6, 'VENDA', 'Cancelado',       FALSE, TRUE),
    (11,  1, 'COMPRA','Pendente',        FALSE, FALSE),
    (12,  2, 'COMPRA','Aprovado',        FALSE, FALSE),
    (13,  3, 'COMPRA','Rejeitado',       FALSE, TRUE),
    (14,  4, 'COMPRA','Concluido',       TRUE,  FALSE)
ON CONFLICT (sk_status) DO NOTHING;


-- =============================================================================
-- 6. TABELAS DE STAGING
--
-- Recebem, a cada ciclo, apenas o recorte incremental extraido do OLTP.
-- Sao truncadas no inicio de cada carga (padrao "truncate and load" no staging).
-- Nao possuem chaves nem indices: privilegiam a velocidade de ingestao via COPY.
-- =============================================================================

CREATE TABLE IF NOT EXISTS stg.produto (
    id_produto INTEGER, cd_produto VARCHAR(25), nm_produto VARCHAR(100),
    nm_categoria VARCHAR(60), nm_subcategoria VARCHAR(60), nm_modelo VARCHAR(60),
    ds_linha VARCHAR(30), ds_classe VARCHAR(30), ds_estilo VARCHAR(30),
    ds_cor VARCHAR(30), ds_tamanho VARCHAR(15), vl_peso NUMERIC(12,2),
    nm_unidade_peso VARCHAR(30), vl_custo_padrao NUMERIC(19,4),
    vl_preco_lista NUMERIC(19,4), fl_fabricacao_propria BOOLEAN,
    fl_produto_acabado BOOLEAN, qt_estoque_seguranca INTEGER,
    qt_ponto_reposicao INTEGER, nr_dias_fabricacao INTEGER,
    dt_inicio_venda DATE, dt_fim_venda DATE, dt_descontinuado DATE,
    dt_modificacao_origem TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stg.cliente (
    id_cliente INTEGER, cd_conta VARCHAR(15), tp_cliente VARCHAR(20),
    nm_cliente VARCHAR(150), nm_primeiro VARCHAR(60), nm_sobrenome VARCHAR(60),
    nm_loja VARCHAR(60), ds_email VARCHAR(80), fl_aceita_promocao BOOLEAN,
    dt_modificacao_origem TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stg.funcionario (
    id_funcionario INTEGER, nm_funcionario VARCHAR(150), ds_cargo VARCHAR(60),
    ds_genero VARCHAR(20), ds_estado_civil VARCHAR(20), dt_nascimento DATE,
    dt_admissao DATE, fl_assalariado BOOLEAN, fl_vendedor BOOLEAN,
    vl_cota_vendas NUMERIC(19,4), vl_bonus NUMERIC(19,4), pc_comissao NUMERIC(10,4),
    dt_modificacao_origem TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stg.territorio (
    id_territorio INTEGER, nm_territorio VARCHAR(60), nm_grupo VARCHAR(60),
    cd_pais CHAR(3), nm_pais VARCHAR(60), vl_vendas_ano_atual NUMERIC(19,4),
    vl_vendas_ano_ante NUMERIC(19,4), vl_custo_ano_atual NUMERIC(19,4),
    dt_modificacao_origem TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stg.geografia (
    id_endereco INTEGER, ds_cidade VARCHAR(60), cd_estado VARCHAR(5),
    nm_estado VARCHAR(60), cd_pais CHAR(3), nm_pais VARCHAR(60),
    nm_regiao VARCHAR(60), cd_postal VARCHAR(15), dt_modificacao_origem TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stg.fornecedor (
    id_fornecedor INTEGER, cd_conta VARCHAR(15), nm_fornecedor VARCHAR(60),
    nr_nivel_credito SMALLINT, fl_fornecedor_ativo BOOLEAN,
    fl_preferencial BOOLEAN, dt_modificacao_origem TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stg.promocao (
    id_promocao INTEGER, ds_promocao VARCHAR(255), tp_promocao VARCHAR(60),
    ds_categoria VARCHAR(60), pc_desconto NUMERIC(10,4), qt_minima INTEGER,
    qt_maxima INTEGER, dt_inicio DATE, dt_fim DATE, dt_modificacao_origem TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stg.metodo_envio (
    id_metodo_envio INTEGER, nm_metodo_envio VARCHAR(60), vl_taxa_base NUMERIC(19,4),
    vl_taxa_por_peso NUMERIC(19,4), dt_modificacao_origem TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stg.venda_item (
    id_item_venda INTEGER, id_pedido INTEGER, nr_pedido VARCHAR(25),
    nr_pedido_cliente VARCHAR(25), dt_pedido DATE, dt_vencimento DATE, dt_envio DATE,
    id_produto INTEGER, id_cliente INTEGER, id_vendedor INTEGER, id_territorio INTEGER,
    id_promocao INTEGER, id_endereco_entrega INTEGER, id_metodo_envio INTEGER,
    fl_pedido_online BOOLEAN, cd_status SMALLINT,
    qt_vendida INTEGER, vl_preco_unitario NUMERIC(19,4),
    pc_desconto_unitario NUMERIC(10,4), vl_custo_unitario NUMERIC(19,4),
    vl_frete_pedido NUMERIC(19,4), vl_imposto_pedido NUMERIC(19,4),
    vl_subtotal_pedido NUMERIC(19,4), dt_modificacao_origem TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stg.compra_item (
    id_item_compra INTEGER, id_ordem_compra INTEGER, dt_pedido DATE,
    dt_previsto DATE, dt_envio DATE, id_produto INTEGER, id_fornecedor INTEGER,
    id_comprador INTEGER, id_metodo_envio INTEGER, cd_status SMALLINT,
    qt_pedida INTEGER, qt_recebida NUMERIC(12,2), qt_rejeitada NUMERIC(12,2),
    vl_preco_unitario NUMERIC(19,4), vl_total_linha NUMERIC(19,4),
    vl_frete_pedido NUMERIC(19,4), vl_imposto_pedido NUMERIC(19,4),
    vl_subtotal_pedido NUMERIC(19,4), dt_modificacao_origem TIMESTAMP
);


-- =============================================================================
-- 7. SEMEADURA DA TABELA DE CONTROLE DA ETL
--
-- Marca d'agua inicial = 1900-01-01, o que faz a PRIMEIRA execucao ser uma
-- carga full. A partir da segunda, so trafegam registros com ModifiedDate
-- superior a marca registrada.
-- =============================================================================

INSERT INTO meta.etl_controle (nm_entidade, ds_tabela_origem, ds_coluna_controle) VALUES
    ('dim_produto',     'Production.Product',              'ModifiedDate'),
    ('dim_cliente',     'Sales.Customer',                  'ModifiedDate'),
    ('dim_funcionario', 'HumanResources.Employee',         'ModifiedDate'),
    ('dim_territorio',  'Sales.SalesTerritory',            'ModifiedDate'),
    ('dim_geografia',   'Person.Address',                  'ModifiedDate'),
    ('dim_fornecedor',  'Purchasing.Vendor',               'ModifiedDate'),
    ('dim_promocao',    'Sales.SpecialOffer',              'ModifiedDate'),
    ('dim_metodo_envio','Purchasing.ShipMethod',           'ModifiedDate'),
    ('fato_vendas',     'Sales.SalesOrderDetail',          'ModifiedDate'),
    ('fato_compras',    'Purchasing.PurchaseOrderDetail',  'ModifiedDate')
ON CONFLICT (nm_entidade) DO NOTHING;
