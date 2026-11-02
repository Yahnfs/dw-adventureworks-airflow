-- =============================================================================
-- DOCUMENTACAO DO MODELO NO CATALOGO DO POSTGRESQL
--
-- Registra a descricao de negocio de cada coluna diretamente em
-- pg_description, por meio de COMMENT ON. Manter a documentacao no proprio
-- banco traz duas vantagens: ela acompanha o objeto em qualquer ambiente para
-- onde o esquema for replicado, e o dicionario de dados
-- (docs/gerar_dicionario.py) pode ser extraido do catalogo, sem risco de
-- divergir da implantacao real.
--
-- Script idempotente; pode ser reexecutado a qualquer momento.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- dw.dim_tempo
-- -----------------------------------------------------------------------------
COMMENT ON COLUMN dw.dim_tempo.dt_data             IS 'Data do calendario (chave natural da dimensao)';
COMMENT ON COLUMN dw.dim_tempo.nr_ano              IS 'Ano com quatro digitos';
COMMENT ON COLUMN dw.dim_tempo.nr_semestre         IS 'Semestre do ano (1 ou 2)';
COMMENT ON COLUMN dw.dim_tempo.nr_trimestre        IS 'Trimestre do ano (1 a 4)';
COMMENT ON COLUMN dw.dim_tempo.nr_mes              IS 'Mes do ano (1 a 12)';
COMMENT ON COLUMN dw.dim_tempo.nr_dia              IS 'Dia do mes (1 a 31)';
COMMENT ON COLUMN dw.dim_tempo.nr_semana_ano       IS 'Semana ISO do ano (1 a 53)';
COMMENT ON COLUMN dw.dim_tempo.nr_dia_semana       IS 'Dia da semana (1 = segunda-feira a 7 = domingo)';
COMMENT ON COLUMN dw.dim_tempo.nr_dia_ano          IS 'Dia sequencial dentro do ano (1 a 366)';
COMMENT ON COLUMN dw.dim_tempo.nm_mes              IS 'Nome do mes por extenso, em portugues';
COMMENT ON COLUMN dw.dim_tempo.nm_mes_abrev        IS 'Abreviacao do nome do mes (tres letras)';
COMMENT ON COLUMN dw.dim_tempo.nm_dia_semana       IS 'Nome do dia da semana por extenso, em portugues';
COMMENT ON COLUMN dw.dim_tempo.ds_ano_mes          IS 'Competencia no formato AAAA-MM, para ordenacao cronologica em relatorios';
COMMENT ON COLUMN dw.dim_tempo.ds_ano_trimestre    IS 'Trimestre no formato AAAA-Qn';
COMMENT ON COLUMN dw.dim_tempo.fl_fim_semana       IS 'Indica se a data cai em sabado ou domingo';
COMMENT ON COLUMN dw.dim_tempo.dt_primeiro_dia_mes IS 'Primeiro dia do mes da data, para agregacoes mensais';
COMMENT ON COLUMN dw.dim_tempo.dt_ultimo_dia_mes   IS 'Ultimo dia do mes da data, para calculos de fechamento';

-- -----------------------------------------------------------------------------
-- dw.dim_produto
-- -----------------------------------------------------------------------------
COMMENT ON COLUMN dw.dim_produto.sk_produto            IS 'Chave substituta; identifica uma VERSAO do produto, nao o produto';
COMMENT ON COLUMN dw.dim_produto.id_produto            IS 'Chave natural (Production.Product.ProductID); repete-se entre versoes';
COMMENT ON COLUMN dw.dim_produto.cd_produto            IS 'Codigo comercial do produto (ProductNumber)';
COMMENT ON COLUMN dw.dim_produto.nm_produto            IS 'Nome comercial do produto';
COMMENT ON COLUMN dw.dim_produto.nm_categoria          IS 'Nivel 1 da hierarquia de produto (Bikes, Components, Clothing, Accessories)';
COMMENT ON COLUMN dw.dim_produto.nm_subcategoria       IS 'Nivel 2 da hierarquia de produto';
COMMENT ON COLUMN dw.dim_produto.nm_modelo             IS 'Nivel 3 da hierarquia: modelo que agrupa variacoes de cor e tamanho';
COMMENT ON COLUMN dw.dim_produto.ds_linha              IS 'Linha do produto (Road, Mountain, Touring, Standard)';
COMMENT ON COLUMN dw.dim_produto.ds_classe             IS 'Classe de posicionamento (Alta, Media, Baixa)';
COMMENT ON COLUMN dw.dim_produto.ds_estilo             IS 'Publico-alvo (Masculino, Feminino, Unissex)';
COMMENT ON COLUMN dw.dim_produto.ds_cor                IS 'Cor do produto';
COMMENT ON COLUMN dw.dim_produto.ds_tamanho            IS 'Tamanho do produto, na unidade do cadastro de origem';
COMMENT ON COLUMN dw.dim_produto.vl_peso               IS 'Peso unitario do produto';
COMMENT ON COLUMN dw.dim_produto.nm_unidade_peso       IS 'Unidade de medida do peso';
COMMENT ON COLUMN dw.dim_produto.vl_custo_padrao       IS 'Custo padrao vigente na versao (atributo monitorado pelo SCD Tipo 2)';
COMMENT ON COLUMN dw.dim_produto.vl_preco_lista        IS 'Preco de tabela vigente na versao (atributo monitorado pelo SCD Tipo 2)';
COMMENT ON COLUMN dw.dim_produto.fl_fabricacao_propria IS 'TRUE para item fabricado internamente; FALSE para item revendido';
COMMENT ON COLUMN dw.dim_produto.fl_produto_acabado    IS 'TRUE para produto acabado, vendavel ao cliente final';
COMMENT ON COLUMN dw.dim_produto.qt_estoque_seguranca  IS 'Estoque minimo de seguranca definido no planejamento';
COMMENT ON COLUMN dw.dim_produto.qt_ponto_reposicao    IS 'Nivel de estoque que dispara nova reposicao';
COMMENT ON COLUMN dw.dim_produto.nr_dias_fabricacao    IS 'Prazo de fabricacao em dias';
COMMENT ON COLUMN dw.dim_produto.dt_inicio_venda       IS 'Data de inicio da comercializacao';
COMMENT ON COLUMN dw.dim_produto.dt_fim_venda          IS 'Data de encerramento da comercializacao';
COMMENT ON COLUMN dw.dim_produto.dt_descontinuado      IS 'Data em que o produto foi descontinuado';
COMMENT ON COLUMN dw.dim_produto.nr_versao             IS 'Numero sequencial da versao do produto (1 = versao original)';
COMMENT ON COLUMN dw.dim_produto.dt_inicio_validade    IS 'Inicio da vigencia da versao; a versao 1 comeca em 1900-01-01';
COMMENT ON COLUMN dw.dim_produto.dt_fim_validade       IS 'Fim da vigencia da versao; 9999-12-31 na versao corrente';
COMMENT ON COLUMN dw.dim_produto.dt_modificacao_origem IS 'ModifiedDate do registro no OLTP que originou esta versao';
COMMENT ON COLUMN dw.dim_produto.dt_carga              IS 'Momento em que a linha foi inserida no DW';
COMMENT ON COLUMN dw.dim_produto.dt_atualizacao        IS 'Momento da ultima alteracao da linha no DW';

-- -----------------------------------------------------------------------------
-- dw.dim_cliente
-- -----------------------------------------------------------------------------
COMMENT ON COLUMN dw.dim_cliente.sk_cliente            IS 'Chave substituta do cliente';
COMMENT ON COLUMN dw.dim_cliente.id_cliente            IS 'Chave natural (Sales.Customer.CustomerID)';
COMMENT ON COLUMN dw.dim_cliente.cd_conta              IS 'Numero da conta comercial do cliente';
COMMENT ON COLUMN dw.dim_cliente.nm_cliente            IS 'Nome do cliente: razao social da loja ou nome da pessoa fisica';
COMMENT ON COLUMN dw.dim_cliente.nm_primeiro           IS 'Primeiro nome, quando o cliente e pessoa fisica';
COMMENT ON COLUMN dw.dim_cliente.nm_sobrenome          IS 'Sobrenome, quando o cliente e pessoa fisica';
COMMENT ON COLUMN dw.dim_cliente.nm_loja               IS 'Nome da loja revendedora, quando aplicavel';
COMMENT ON COLUMN dw.dim_cliente.ds_email              IS 'Endereco de correio eletronico principal';
COMMENT ON COLUMN dw.dim_cliente.fl_aceita_promocao    IS 'Indica aceite de comunicacao promocional (EmailPromotion > 0)';
COMMENT ON COLUMN dw.dim_cliente.hash_scd              IS 'MD5 dos atributos; usado para evitar escrita quando nada mudou';
COMMENT ON COLUMN dw.dim_cliente.dt_modificacao_origem IS 'ModifiedDate do registro no OLTP';
COMMENT ON COLUMN dw.dim_cliente.dt_carga              IS 'Momento em que a linha foi inserida no DW';
COMMENT ON COLUMN dw.dim_cliente.dt_atualizacao        IS 'Momento da ultima sobrescrita da linha (SCD Tipo 1)';

-- -----------------------------------------------------------------------------
-- dw.dim_funcionario
-- -----------------------------------------------------------------------------
COMMENT ON COLUMN dw.dim_funcionario.sk_funcionario        IS 'Chave substituta do funcionario';
COMMENT ON COLUMN dw.dim_funcionario.id_funcionario        IS 'Chave natural (HumanResources.Employee.BusinessEntityID)';
COMMENT ON COLUMN dw.dim_funcionario.nm_funcionario        IS 'Nome completo do funcionario';
COMMENT ON COLUMN dw.dim_funcionario.ds_cargo              IS 'Cargo ocupado';
COMMENT ON COLUMN dw.dim_funcionario.ds_genero             IS 'Genero declarado no cadastro funcional';
COMMENT ON COLUMN dw.dim_funcionario.ds_estado_civil       IS 'Estado civil declarado no cadastro funcional';
COMMENT ON COLUMN dw.dim_funcionario.dt_nascimento         IS 'Data de nascimento';
COMMENT ON COLUMN dw.dim_funcionario.dt_admissao           IS 'Data de admissao na empresa';
COMMENT ON COLUMN dw.dim_funcionario.fl_assalariado        IS 'TRUE para regime assalariado; FALSE para horista';
COMMENT ON COLUMN dw.dim_funcionario.fl_vendedor           IS 'TRUE quando o funcionario integra a forca de vendas (Sales.SalesPerson)';
COMMENT ON COLUMN dw.dim_funcionario.vl_cota_vendas        IS 'Cota de vendas atribuida; nulo para nao vendedores';
COMMENT ON COLUMN dw.dim_funcionario.vl_bonus              IS 'Bonificacao acordada para o vendedor';
COMMENT ON COLUMN dw.dim_funcionario.pc_comissao           IS 'Percentual de comissao sobre vendas';
COMMENT ON COLUMN dw.dim_funcionario.hash_scd              IS 'MD5 dos atributos monitorados';
COMMENT ON COLUMN dw.dim_funcionario.dt_modificacao_origem IS 'ModifiedDate do registro no OLTP';
COMMENT ON COLUMN dw.dim_funcionario.dt_carga              IS 'Momento em que a linha foi inserida no DW';
COMMENT ON COLUMN dw.dim_funcionario.dt_atualizacao        IS 'Momento da ultima sobrescrita da linha (SCD Tipo 1)';

-- -----------------------------------------------------------------------------
-- dw.dim_territorio
-- -----------------------------------------------------------------------------
COMMENT ON COLUMN dw.dim_territorio.sk_territorio         IS 'Chave substituta do territorio';
COMMENT ON COLUMN dw.dim_territorio.id_territorio         IS 'Chave natural (Sales.SalesTerritory.TerritoryID)';
COMMENT ON COLUMN dw.dim_territorio.nm_territorio         IS 'Nome do territorio comercial';
COMMENT ON COLUMN dw.dim_territorio.nm_grupo              IS 'Agrupamento continental do territorio (North America, Europe, Pacific)';
COMMENT ON COLUMN dw.dim_territorio.cd_pais               IS 'Codigo ISO do pais do territorio';
COMMENT ON COLUMN dw.dim_territorio.nm_pais               IS 'Nome do pais do territorio';
COMMENT ON COLUMN dw.dim_territorio.vl_vendas_ano_atual   IS 'Vendas acumuladas no ano corrente, conforme o cadastro de origem';
COMMENT ON COLUMN dw.dim_territorio.vl_vendas_ano_ante    IS 'Vendas do ano anterior, conforme o cadastro de origem';
COMMENT ON COLUMN dw.dim_territorio.vl_custo_ano_atual    IS 'Custo acumulado no ano corrente, conforme o cadastro de origem';
COMMENT ON COLUMN dw.dim_territorio.hash_scd              IS 'MD5 dos atributos monitorados';
COMMENT ON COLUMN dw.dim_territorio.dt_modificacao_origem IS 'ModifiedDate do registro no OLTP';
COMMENT ON COLUMN dw.dim_territorio.dt_carga              IS 'Momento em que a linha foi inserida no DW';
COMMENT ON COLUMN dw.dim_territorio.dt_atualizacao        IS 'Momento da ultima sobrescrita da linha (SCD Tipo 1)';

-- -----------------------------------------------------------------------------
-- dw.dim_geografia
-- -----------------------------------------------------------------------------
COMMENT ON COLUMN dw.dim_geografia.sk_geografia          IS 'Chave substituta da localidade';
COMMENT ON COLUMN dw.dim_geografia.id_endereco           IS 'Chave natural (Person.Address.AddressID)';
COMMENT ON COLUMN dw.dim_geografia.ds_cidade             IS 'Municipio do endereco';
COMMENT ON COLUMN dw.dim_geografia.cd_estado             IS 'Sigla do estado ou provincia';
COMMENT ON COLUMN dw.dim_geografia.nm_estado             IS 'Nome do estado ou provincia';
COMMENT ON COLUMN dw.dim_geografia.cd_pais               IS 'Codigo ISO do pais';
COMMENT ON COLUMN dw.dim_geografia.nm_pais               IS 'Nome do pais';
COMMENT ON COLUMN dw.dim_geografia.nm_regiao             IS 'Agrupamento continental do territorio associado ao estado';
COMMENT ON COLUMN dw.dim_geografia.cd_postal             IS 'Codigo postal do endereco';
COMMENT ON COLUMN dw.dim_geografia.hash_scd              IS 'MD5 dos atributos monitorados';
COMMENT ON COLUMN dw.dim_geografia.dt_modificacao_origem IS 'ModifiedDate do registro no OLTP';
COMMENT ON COLUMN dw.dim_geografia.dt_carga              IS 'Momento em que a linha foi inserida no DW';
COMMENT ON COLUMN dw.dim_geografia.dt_atualizacao        IS 'Momento da ultima sobrescrita da linha (SCD Tipo 1)';

-- -----------------------------------------------------------------------------
-- dw.dim_fornecedor
-- -----------------------------------------------------------------------------
COMMENT ON COLUMN dw.dim_fornecedor.sk_fornecedor         IS 'Chave substituta do fornecedor';
COMMENT ON COLUMN dw.dim_fornecedor.id_fornecedor         IS 'Chave natural (Purchasing.Vendor.BusinessEntityID)';
COMMENT ON COLUMN dw.dim_fornecedor.cd_conta              IS 'Numero da conta do fornecedor';
COMMENT ON COLUMN dw.dim_fornecedor.nm_fornecedor         IS 'Razao social do fornecedor';
COMMENT ON COLUMN dw.dim_fornecedor.nr_nivel_credito      IS 'Nivel de credito de 1 (melhor) a 5 (pior)';
COMMENT ON COLUMN dw.dim_fornecedor.ds_nivel_credito      IS 'Descricao textual do nivel de credito, derivada na ETL';
COMMENT ON COLUMN dw.dim_fornecedor.fl_fornecedor_ativo   IS 'TRUE enquanto o fornecedor esta habilitado a receber pedidos';
COMMENT ON COLUMN dw.dim_fornecedor.fl_preferencial       IS 'TRUE para fornecedor com condicao preferencial de compra';
COMMENT ON COLUMN dw.dim_fornecedor.hash_scd              IS 'MD5 dos atributos monitorados';
COMMENT ON COLUMN dw.dim_fornecedor.dt_modificacao_origem IS 'ModifiedDate do registro no OLTP';
COMMENT ON COLUMN dw.dim_fornecedor.dt_carga              IS 'Momento em que a linha foi inserida no DW';
COMMENT ON COLUMN dw.dim_fornecedor.dt_atualizacao        IS 'Momento da ultima sobrescrita da linha (SCD Tipo 1)';

-- -----------------------------------------------------------------------------
-- dw.dim_promocao
-- -----------------------------------------------------------------------------
COMMENT ON COLUMN dw.dim_promocao.sk_promocao           IS 'Chave substituta da oferta';
COMMENT ON COLUMN dw.dim_promocao.id_promocao           IS 'Chave natural (Sales.SpecialOffer.SpecialOfferID)';
COMMENT ON COLUMN dw.dim_promocao.ds_promocao           IS 'Descricao comercial da oferta';
COMMENT ON COLUMN dw.dim_promocao.tp_promocao           IS 'Mecanica da oferta (por volume, sazonal, excedente etc.)';
COMMENT ON COLUMN dw.dim_promocao.ds_categoria          IS 'Publico da oferta (Reseller ou Customer)';
COMMENT ON COLUMN dw.dim_promocao.pc_desconto           IS 'Percentual de desconto previsto na oferta';
COMMENT ON COLUMN dw.dim_promocao.qt_minima             IS 'Quantidade minima para habilitar a oferta';
COMMENT ON COLUMN dw.dim_promocao.qt_maxima             IS 'Quantidade maxima coberta pela oferta';
COMMENT ON COLUMN dw.dim_promocao.dt_inicio             IS 'Inicio da vigencia da oferta';
COMMENT ON COLUMN dw.dim_promocao.dt_fim                IS 'Fim da vigencia da oferta';
COMMENT ON COLUMN dw.dim_promocao.hash_scd              IS 'MD5 dos atributos monitorados';
COMMENT ON COLUMN dw.dim_promocao.dt_modificacao_origem IS 'ModifiedDate do registro no OLTP';
COMMENT ON COLUMN dw.dim_promocao.dt_carga              IS 'Momento em que a linha foi inserida no DW';
COMMENT ON COLUMN dw.dim_promocao.dt_atualizacao        IS 'Momento da ultima sobrescrita da linha (SCD Tipo 1)';

-- -----------------------------------------------------------------------------
-- dw.dim_metodo_envio
-- -----------------------------------------------------------------------------
COMMENT ON TABLE  dw.dim_metodo_envio                       IS 'Dimensao conformada de modalidade de frete, compartilhada por vendas e compras';
COMMENT ON TABLE  dw.dim_promocao                           IS 'Dimensao promocao (SCD Tipo 1): oferta aplicada a cada item de venda';
COMMENT ON COLUMN dw.dim_metodo_envio.sk_metodo_envio       IS 'Chave substituta da modalidade de frete';
COMMENT ON COLUMN dw.dim_metodo_envio.id_metodo_envio       IS 'Chave natural (Purchasing.ShipMethod.ShipMethodID)';
COMMENT ON COLUMN dw.dim_metodo_envio.nm_metodo_envio       IS 'Nome da transportadora ou modalidade de entrega';
COMMENT ON COLUMN dw.dim_metodo_envio.vl_taxa_base          IS 'Taxa fixa cobrada por remessa';
COMMENT ON COLUMN dw.dim_metodo_envio.vl_taxa_por_peso      IS 'Taxa variavel cobrada por unidade de peso';
COMMENT ON COLUMN dw.dim_metodo_envio.hash_scd              IS 'MD5 dos atributos monitorados';
COMMENT ON COLUMN dw.dim_metodo_envio.dt_modificacao_origem IS 'ModifiedDate do registro no OLTP';
COMMENT ON COLUMN dw.dim_metodo_envio.dt_carga              IS 'Momento em que a linha foi inserida no DW';
COMMENT ON COLUMN dw.dim_metodo_envio.dt_atualizacao        IS 'Momento da ultima sobrescrita da linha (SCD Tipo 1)';

-- -----------------------------------------------------------------------------
-- dw.dim_canal_venda e dw.dim_status_pedido
-- -----------------------------------------------------------------------------
COMMENT ON TABLE  dw.dim_canal_venda            IS 'Dimensao estatica de canal de venda, derivada de SalesOrderHeader.OnlineOrderFlag';
COMMENT ON COLUMN dw.dim_canal_venda.sk_canal   IS 'Chave substituta do canal (-1 nao informado, 1 Internet, 2 Revenda)';
COMMENT ON COLUMN dw.dim_canal_venda.cd_canal   IS 'Codigo mnemonico do canal';
COMMENT ON COLUMN dw.dim_canal_venda.nm_canal   IS 'Nome do canal de venda';
COMMENT ON COLUMN dw.dim_canal_venda.ds_canal   IS 'Regra de negocio que define o enquadramento no canal';

COMMENT ON TABLE  dw.dim_status_pedido              IS 'Dimensao estatica de situacao do pedido, compartilhada por vendas e compras';
COMMENT ON COLUMN dw.dim_status_pedido.sk_status    IS 'Chave substituta da situacao';
COMMENT ON COLUMN dw.dim_status_pedido.cd_status    IS 'Codigo numerico da situacao no sistema de origem';
COMMENT ON COLUMN dw.dim_status_pedido.nm_status    IS 'Descricao da situacao em portugues';
COMMENT ON COLUMN dw.dim_status_pedido.fl_concluido IS 'TRUE quando a situacao representa um ciclo concluido com sucesso';
COMMENT ON COLUMN dw.dim_status_pedido.fl_cancelado IS 'TRUE quando a situacao representa cancelamento ou rejeicao';

-- -----------------------------------------------------------------------------
-- dw.fato_vendas
-- -----------------------------------------------------------------------------
COMMENT ON COLUMN dw.fato_vendas.sk_fato_vendas        IS 'Chave substituta da linha de fato';
COMMENT ON COLUMN dw.fato_vendas.sk_tempo_pedido       IS 'Data em que o pedido foi realizado (papel principal da dimensao tempo)';
COMMENT ON COLUMN dw.fato_vendas.sk_tempo_vencimento   IS 'Data prometida de entrega (papel de prazo da dimensao tempo)';
COMMENT ON COLUMN dw.fato_vendas.sk_tempo_envio        IS 'Data efetiva de expedicao; aponta para -1 enquanto o pedido nao e expedido';
COMMENT ON COLUMN dw.fato_vendas.sk_produto            IS 'Versao do produto vigente na data do pedido (SCD Tipo 2)';
COMMENT ON COLUMN dw.fato_vendas.sk_cliente            IS 'Cliente que realizou a compra';
COMMENT ON COLUMN dw.fato_vendas.sk_vendedor           IS 'Vendedor responsavel; -1 nas vendas pela internet, que nao possuem vendedor';
COMMENT ON COLUMN dw.fato_vendas.sk_territorio         IS 'Territorio comercial ao qual o pedido foi atribuido';
COMMENT ON COLUMN dw.fato_vendas.sk_promocao           IS 'Oferta aplicada a linha; a oferta neutra "No Discount" e o padrao';
COMMENT ON COLUMN dw.fato_vendas.sk_geografia_entrega  IS 'Localidade do endereco de entrega';
COMMENT ON COLUMN dw.fato_vendas.sk_metodo_envio       IS 'Modalidade de frete contratada';
COMMENT ON COLUMN dw.fato_vendas.sk_canal              IS 'Canal de venda (Internet ou Revenda)';
COMMENT ON COLUMN dw.fato_vendas.sk_status             IS 'Situacao do pedido no dominio VENDA';
COMMENT ON COLUMN dw.fato_vendas.id_pedido             IS 'Dimensao degenerada: identificador do pedido de venda';
COMMENT ON COLUMN dw.fato_vendas.nr_pedido             IS 'Dimensao degenerada: numero do pedido apresentado ao cliente';
COMMENT ON COLUMN dw.fato_vendas.nr_pedido_cliente     IS 'Dimensao degenerada: numero da ordem de compra emitida pelo cliente';
COMMENT ON COLUMN dw.fato_vendas.qt_vendida            IS 'Quantidade de unidades vendidas na linha (metrica aditiva)';
COMMENT ON COLUMN dw.fato_vendas.vl_preco_unitario     IS 'Preco unitario praticado (metrica nao aditiva; usar media ponderada)';
COMMENT ON COLUMN dw.fato_vendas.pc_desconto_unitario  IS 'Percentual de desconto aplicado a linha (metrica nao aditiva)';
COMMENT ON COLUMN dw.fato_vendas.vl_desconto           IS 'Valor monetario do desconto concedido na linha (metrica aditiva)';
COMMENT ON COLUMN dw.fato_vendas.vl_custo_unitario     IS 'Custo padrao do produto vigente na data do pedido (ProductCostHistory)';
COMMENT ON COLUMN dw.fato_vendas.vl_custo_total        IS 'qt_vendida * vl_custo_unitario (metrica aditiva)';
COMMENT ON COLUMN dw.fato_vendas.vl_imposto_rateado    IS 'Imposto do cabecalho do pedido rateado pela participacao da linha na receita';
COMMENT ON COLUMN dw.fato_vendas.qt_dias_entrega       IS 'Dias decorridos entre a data do pedido e a data de envio';
COMMENT ON COLUMN dw.fato_vendas.qt_dias_atraso        IS 'Dias de atraso em relacao a data prometida; zero quando dentro do prazo';
COMMENT ON COLUMN dw.fato_vendas.fl_entrega_atrasada   IS 'TRUE quando a data de envio superou a data prometida';
COMMENT ON COLUMN dw.fato_vendas.fl_pedido_online      IS 'Copia desnormalizada do canal, para filtros diretos sem juncao';
COMMENT ON COLUMN dw.fato_vendas.dt_modificacao_origem IS 'Maior ModifiedDate entre o item e o cabecalho; base da carga incremental';
COMMENT ON COLUMN dw.fato_vendas.dt_carga              IS 'Momento em que a linha foi inserida no DW';
COMMENT ON COLUMN dw.fato_vendas.dt_atualizacao        IS 'Momento da ultima atualizacao da linha no DW';

-- -----------------------------------------------------------------------------
-- dw.fato_compras
-- -----------------------------------------------------------------------------
COMMENT ON COLUMN dw.fato_compras.sk_fato_compras         IS 'Chave substituta da linha de fato';
COMMENT ON COLUMN dw.fato_compras.sk_tempo_pedido         IS 'Data de emissao da ordem de compra';
COMMENT ON COLUMN dw.fato_compras.sk_tempo_previsto       IS 'Data prevista de entrega pelo fornecedor';
COMMENT ON COLUMN dw.fato_compras.sk_tempo_recebimento    IS 'Data efetiva de recebimento; -1 enquanto pendente';
COMMENT ON COLUMN dw.fato_compras.sk_produto              IS 'Versao do produto vigente na data da ordem (SCD Tipo 2)';
COMMENT ON COLUMN dw.fato_compras.sk_fornecedor           IS 'Fornecedor responsavel pelo item';
COMMENT ON COLUMN dw.fato_compras.sk_metodo_envio         IS 'Modalidade de frete contratada';
COMMENT ON COLUMN dw.fato_compras.sk_status               IS 'Situacao da ordem no dominio COMPRA';
COMMENT ON COLUMN dw.fato_compras.id_item_compra          IS 'Dimensao degenerada e chave de negocio usada no MERGE incremental';
COMMENT ON COLUMN dw.fato_compras.id_ordem_compra         IS 'Dimensao degenerada: identificador da ordem de compra';
COMMENT ON COLUMN dw.fato_compras.qt_pedida               IS 'Quantidade solicitada ao fornecedor (metrica aditiva)';
COMMENT ON COLUMN dw.fato_compras.qt_recebida             IS 'Quantidade efetivamente recebida (metrica aditiva)';
COMMENT ON COLUMN dw.fato_compras.qt_rejeitada            IS 'Quantidade recusada na inspecao de qualidade (metrica aditiva)';
COMMENT ON COLUMN dw.fato_compras.vl_preco_unitario       IS 'Preco unitario negociado (metrica nao aditiva)';
COMMENT ON COLUMN dw.fato_compras.vl_total_linha          IS 'Valor total da linha da ordem de compra (metrica aditiva)';
COMMENT ON COLUMN dw.fato_compras.vl_frete_rateado        IS 'Frete do cabecalho rateado pela participacao da linha no subtotal';
COMMENT ON COLUMN dw.fato_compras.vl_imposto_rateado      IS 'Imposto do cabecalho rateado pela participacao da linha no subtotal';
COMMENT ON COLUMN dw.fato_compras.qt_dias_recebimento     IS 'Dias decorridos entre a emissao da ordem e o recebimento';
COMMENT ON COLUMN dw.fato_compras.qt_dias_atraso          IS 'Dias de atraso em relacao a data prevista; zero quando dentro do prazo';
COMMENT ON COLUMN dw.fato_compras.fl_recebimento_atrasado IS 'TRUE quando o recebimento superou a data prevista';
COMMENT ON COLUMN dw.fato_compras.dt_modificacao_origem   IS 'Maior ModifiedDate entre o item e o cabecalho; base da carga incremental';
COMMENT ON COLUMN dw.fato_compras.dt_carga                IS 'Momento em que a linha foi inserida no DW';
COMMENT ON COLUMN dw.fato_compras.dt_atualizacao          IS 'Momento da ultima atualizacao da linha no DW';

-- -----------------------------------------------------------------------------
-- meta
-- -----------------------------------------------------------------------------
COMMENT ON COLUMN meta.etl_controle.nm_entidade          IS 'Entidade do DW a que a marca d''agua se refere';
COMMENT ON COLUMN meta.etl_controle.ds_tabela_origem     IS 'Tabela do OLTP que alimenta a entidade';
COMMENT ON COLUMN meta.etl_controle.ds_coluna_controle   IS 'Coluna de auditoria usada como criterio de incremento';
COMMENT ON COLUMN meta.etl_controle.qt_registros_total   IS 'Volume acumulado de registros processados desde a implantacao';
COMMENT ON COLUMN meta.etl_controle.dt_atualizacao       IS 'Momento da ultima atualizacao da marca d''agua';

COMMENT ON COLUMN meta.etl_execucao.id_execucao       IS 'Identificador sequencial da linha de log';
COMMENT ON COLUMN meta.etl_execucao.nm_entidade       IS 'Entidade processada nesta linha de log';
COMMENT ON COLUMN meta.etl_execucao.ds_fase           IS 'DIMENSAO ou FATO';
COMMENT ON COLUMN meta.etl_execucao.dt_inicio         IS 'Inicio do processamento da entidade';
COMMENT ON COLUMN meta.etl_execucao.dt_fim            IS 'Termino do processamento da entidade';
COMMENT ON COLUMN meta.etl_execucao.qt_extraidos      IS 'Registros trazidos do OLTP na janela incremental';
COMMENT ON COLUMN meta.etl_execucao.qt_inseridos      IS 'Registros novos gravados no DW';
COMMENT ON COLUMN meta.etl_execucao.qt_atualizados    IS 'Registros existentes efetivamente alterados no DW';
COMMENT ON COLUMN meta.etl_execucao.ds_marca_agua_de  IS 'Limite inferior da janela processada';
COMMENT ON COLUMN meta.etl_execucao.ds_marca_agua_ate IS 'Maior ModifiedDate observado no lote; nova marca d''agua';
COMMENT ON COLUMN meta.etl_execucao.ds_status         IS 'EM_EXECUCAO, SUCESSO, SEM_ALTERACAO ou ERRO';
COMMENT ON COLUMN meta.etl_execucao.ds_mensagem       IS 'Detalhe do erro, quando houver';
