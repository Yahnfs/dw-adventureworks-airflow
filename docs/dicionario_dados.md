# Dicionario de dados - Data Warehouse AdventureWorks

> Gerado por `docs/gerar_dicionario.py` a partir do catalogo do PostgreSQL.

## Convencoes de nomenclatura

| Prefixo | Significado | Exemplo |
|---|---|---|
| `sk_` | chave substituta gerada pelo DW | `sk_produto` |
| `id_` | chave natural herdada da origem | `id_produto` |
| `cd_` | codigo alfanumerico de negocio | `cd_produto` |
| `nm_` | nome ou descritor curto | `nm_categoria` |
| `ds_` | descricao textual | `ds_cargo` |
| `tp_` | tipo ou classificacao | `tp_cliente` |
| `dt_` | data ou data e hora | `dt_pedido` |
| `vl_` | valor monetario, em dolares americanos (US$) | `vl_liquido` |
| `qt_` | quantidade | `qt_vendida` |
| `pc_` | percentual | `pc_desconto_unitario` |
| `nr_` | numero sequencial ou ordinal | `nr_versao` |
| `fl_` | indicador logico | `fl_corrente` |


## Camada dimensional (`dw`)

### `dw.fato_compras`

Fato transacional de compras; grao = item de ordem de compra (Purchasing.PurchaseOrderDetail)

**Linhas carregadas:** 8.845

| Coluna | Tipo | Nulo | Chave | Descricao |
|---|---|---|---|---|
| `sk_fato_compras` | bigint | nao | PK | Chave substituta da linha de fato |
| `sk_tempo_pedido` | integer | nao | FK -> dw.dim_tempo | Data de emissao da ordem de compra |
| `sk_tempo_previsto` | integer | nao | FK -> dw.dim_tempo | Data prevista de entrega pelo fornecedor |
| `sk_tempo_recebimento` | integer | nao | FK -> dw.dim_tempo | Data efetiva de recebimento; -1 enquanto pendente |
| `sk_produto` | bigint | nao | FK -> dw.dim_produto | Versao do produto vigente na data da ordem (SCD Tipo 2) |
| `sk_fornecedor` | bigint | nao | FK -> dw.dim_fornecedor | Fornecedor responsavel pelo item |
| `sk_comprador` | bigint | nao | FK -> dw.dim_funcionario | Papel de COMPRADOR da dimensao conformada dw.dim_funcionario |
| `sk_metodo_envio` | bigint | nao | FK -> dw.dim_metodo_envio | Modalidade de frete contratada |
| `sk_status` | integer | nao | FK -> dw.dim_status_pedido | Situacao da ordem no dominio COMPRA |
| `id_item_compra` | integer | nao |  | Dimensao degenerada e chave de negocio usada no MERGE incremental |
| `id_ordem_compra` | integer | nao |  | Dimensao degenerada: identificador da ordem de compra |
| `qt_pedida` | integer | nao |  | Quantidade solicitada ao fornecedor (metrica aditiva) |
| `qt_recebida` | numeric(12,2) | nao |  | Quantidade efetivamente recebida (metrica aditiva) |
| `qt_rejeitada` | numeric(12,2) | nao |  | Quantidade recusada na inspecao de qualidade (metrica aditiva) |
| `qt_aceita` | numeric(12,2) | nao |  | qt_recebida - qt_rejeitada |
| `vl_preco_unitario` | numeric(19,4) | nao |  | Preco unitario negociado (metrica nao aditiva) |
| `vl_total_linha` | numeric(19,4) | nao |  | Valor total da linha da ordem de compra (metrica aditiva) |
| `vl_frete_rateado` | numeric(19,4) | nao |  | Frete do cabecalho rateado pela participacao da linha no subtotal |
| `vl_imposto_rateado` | numeric(19,4) | nao |  | Imposto do cabecalho rateado pela participacao da linha no subtotal |
| `qt_dias_recebimento` | integer | sim |  | Dias decorridos entre a emissao da ordem e o recebimento |
| `qt_dias_atraso` | integer | sim |  | Dias de atraso em relacao a data prevista; zero quando dentro do prazo |
| `fl_recebimento_atrasado` | boolean | nao |  | TRUE quando o recebimento superou a data prevista |
| `dt_modificacao_origem` | timestamp without time zone | nao |  | Maior ModifiedDate entre o item e o cabecalho; base da carga incremental |
| `dt_carga` | timestamp without time zone | nao |  | Momento em que a linha foi inserida no DW |
| `dt_atualizacao` | timestamp without time zone | nao |  | Momento da ultima atualizacao da linha no DW |

### `dw.fato_vendas`

Fato transacional de vendas; grao = item de pedido (Sales.SalesOrderDetail)

**Linhas carregadas:** 121.317

| Coluna | Tipo | Nulo | Chave | Descricao |
|---|---|---|---|---|
| `sk_fato_vendas` | bigint | nao | PK | Chave substituta da linha de fato |
| `sk_tempo_pedido` | integer | nao | FK -> dw.dim_tempo | Data em que o pedido foi realizado (papel principal da dimensao tempo) |
| `sk_tempo_vencimento` | integer | nao | FK -> dw.dim_tempo | Data prometida de entrega (papel de prazo da dimensao tempo) |
| `sk_tempo_envio` | integer | nao | FK -> dw.dim_tempo | Data efetiva de expedicao; aponta para -1 enquanto o pedido nao e expedido |
| `sk_produto` | bigint | nao | FK -> dw.dim_produto | Versao do produto vigente na data do pedido (SCD Tipo 2) |
| `sk_cliente` | bigint | nao | FK -> dw.dim_cliente | Cliente que realizou a compra |
| `sk_vendedor` | bigint | nao | FK -> dw.dim_funcionario | Vendedor responsavel; -1 nas vendas pela internet, que nao possuem vendedor |
| `sk_territorio` | bigint | nao | FK -> dw.dim_territorio | Territorio comercial ao qual o pedido foi atribuido |
| `sk_promocao` | bigint | nao | FK -> dw.dim_promocao | Oferta aplicada a linha; a oferta neutra "No Discount" e o padrao |
| `sk_geografia_entrega` | bigint | nao | FK -> dw.dim_geografia | Localidade do endereco de entrega |
| `sk_metodo_envio` | bigint | nao | FK -> dw.dim_metodo_envio | Modalidade de frete contratada |
| `sk_canal` | integer | nao | FK -> dw.dim_canal_venda | Canal de venda (Internet ou Revenda) |
| `sk_status` | integer | nao | FK -> dw.dim_status_pedido | Situacao do pedido no dominio VENDA |
| `id_item_venda` | integer | nao |  | Dimensao degenerada e chave de negocio usada no MERGE incremental |
| `id_pedido` | integer | nao |  | Dimensao degenerada: identificador do pedido de venda |
| `nr_pedido` | character varying(25) | nao |  | Dimensao degenerada: numero do pedido apresentado ao cliente |
| `nr_pedido_cliente` | character varying(25) | sim |  | Dimensao degenerada: numero da ordem de compra emitida pelo cliente |
| `qt_vendida` | integer | nao |  | Quantidade de unidades vendidas na linha (metrica aditiva) |
| `vl_preco_unitario` | numeric(19,4) | nao |  | Preco unitario praticado (metrica nao aditiva; usar media ponderada) |
| `pc_desconto_unitario` | numeric(10,4) | nao |  | Percentual de desconto aplicado a linha (metrica nao aditiva) |
| `vl_bruto` | numeric(19,4) | nao |  | qt_vendida * vl_preco_unitario (antes do desconto) |
| `vl_desconto` | numeric(19,4) | nao |  | Valor monetario do desconto concedido na linha (metrica aditiva) |
| `vl_liquido` | numeric(19,4) | nao |  | Receita liquida da linha: vl_bruto - vl_desconto |
| `vl_custo_unitario` | numeric(19,4) | nao |  | Custo padrao do produto vigente na data do pedido (ProductCostHistory) |
| `vl_custo_total` | numeric(19,4) | nao |  | qt_vendida * vl_custo_unitario (metrica aditiva) |
| `vl_margem_bruta` | numeric(19,4) | nao |  | vl_liquido - vl_custo_total |
| `vl_frete_rateado` | numeric(19,4) | nao |  | Frete do cabecalho do pedido rateado pela participacao da linha na receita |
| `vl_imposto_rateado` | numeric(19,4) | nao |  | Imposto do cabecalho do pedido rateado pela participacao da linha na receita |
| `qt_dias_entrega` | integer | sim |  | Dias decorridos entre a data do pedido e a data de envio |
| `qt_dias_atraso` | integer | sim |  | Dias de atraso em relacao a data prometida; zero quando dentro do prazo |
| `fl_entrega_atrasada` | boolean | nao |  | TRUE quando a data de envio superou a data prometida |
| `fl_pedido_online` | boolean | nao |  | Copia desnormalizada do canal, para filtros diretos sem juncao |
| `dt_modificacao_origem` | timestamp without time zone | nao |  | Maior ModifiedDate entre o item e o cabecalho; base da carga incremental |
| `dt_carga` | timestamp without time zone | nao |  | Momento em que a linha foi inserida no DW |
| `dt_atualizacao` | timestamp without time zone | nao |  | Momento da ultima atualizacao da linha no DW |

### `dw.dim_canal_venda`

Dimensao estatica de canal de venda, derivada de SalesOrderHeader.OnlineOrderFlag

**Linhas carregadas:** 3

| Coluna | Tipo | Nulo | Chave | Descricao |
|---|---|---|---|---|
| `sk_canal` | integer | nao | PK | Chave substituta do canal (-1 nao informado, 1 Internet, 2 Revenda) |
| `cd_canal` | character varying(15) | nao |  | Codigo mnemonico do canal |
| `nm_canal` | character varying(60) | nao |  | Nome do canal de venda |
| `ds_canal` | character varying(255) | sim |  | Regra de negocio que define o enquadramento no canal |

### `dw.dim_cliente`

Dimensao cliente (SCD Tipo 1), unificando pessoa fisica e loja revendedora

**Linhas carregadas:** 19.821

| Coluna | Tipo | Nulo | Chave | Descricao |
|---|---|---|---|---|
| `sk_cliente` | bigint | nao | PK | Chave substituta do cliente |
| `id_cliente` | integer | nao |  | Chave natural (Sales.Customer.CustomerID) |
| `cd_conta` | character varying(15) | sim |  | Numero da conta comercial do cliente |
| `tp_cliente` | character varying(20) | nao |  | Pessoa Fisica \| Loja - segmenta os canais Internet e Revenda |
| `nm_cliente` | character varying(150) | nao |  | Nome do cliente: razao social da loja ou nome da pessoa fisica |
| `nm_primeiro` | character varying(60) | sim |  | Primeiro nome, quando o cliente e pessoa fisica |
| `nm_sobrenome` | character varying(60) | sim |  | Sobrenome, quando o cliente e pessoa fisica |
| `nm_loja` | character varying(60) | sim |  | Nome da loja revendedora, quando aplicavel |
| `ds_email` | character varying(80) | sim |  | Endereco de correio eletronico principal |
| `fl_aceita_promocao` | boolean | nao |  | Indica aceite de comunicacao promocional (EmailPromotion > 0) |
| `hash_scd` | character(32) | nao |  | MD5 dos atributos; usado para evitar escrita quando nada mudou |
| `dt_modificacao_origem` | timestamp without time zone | sim |  | ModifiedDate do registro no OLTP |
| `dt_carga` | timestamp without time zone | nao |  | Momento em que a linha foi inserida no DW |
| `dt_atualizacao` | timestamp without time zone | nao |  | Momento da ultima sobrescrita da linha (SCD Tipo 1) |

### `dw.dim_fornecedor`

Dimensao fornecedor, utilizada pela fato_compras

**Linhas carregadas:** 105

| Coluna | Tipo | Nulo | Chave | Descricao |
|---|---|---|---|---|
| `sk_fornecedor` | bigint | nao | PK | Chave substituta do fornecedor |
| `id_fornecedor` | integer | nao |  | Chave natural (Purchasing.Vendor.BusinessEntityID) |
| `cd_conta` | character varying(15) | sim |  | Numero da conta do fornecedor |
| `nm_fornecedor` | character varying(60) | nao |  | Razao social do fornecedor |
| `nr_nivel_credito` | smallint | sim |  | Nivel de credito de 1 (melhor) a 5 (pior) |
| `ds_nivel_credito` | character varying(20) | sim |  | Descricao textual do nivel de credito, derivada na ETL |
| `fl_fornecedor_ativo` | boolean | nao |  | TRUE enquanto o fornecedor esta habilitado a receber pedidos |
| `fl_preferencial` | boolean | nao |  | TRUE para fornecedor com condicao preferencial de compra |
| `hash_scd` | character(32) | nao |  | MD5 dos atributos monitorados |
| `dt_modificacao_origem` | timestamp without time zone | sim |  | ModifiedDate do registro no OLTP |
| `dt_carga` | timestamp without time zone | nao |  | Momento em que a linha foi inserida no DW |
| `dt_atualizacao` | timestamp without time zone | nao |  | Momento da ultima sobrescrita da linha (SCD Tipo 1) |

### `dw.dim_funcionario`

Dimensao funcionario (SCD Tipo 1) de multiplos papeis: vendedor em fato_vendas e comprador em fato_compras

**Linhas carregadas:** 291

| Coluna | Tipo | Nulo | Chave | Descricao |
|---|---|---|---|---|
| `sk_funcionario` | bigint | nao | PK | Chave substituta do funcionario |
| `id_funcionario` | integer | nao |  | Chave natural (HumanResources.Employee.BusinessEntityID) |
| `nm_funcionario` | character varying(150) | nao |  | Nome completo do funcionario |
| `ds_cargo` | character varying(60) | sim |  | Cargo ocupado |
| `ds_genero` | character varying(20) | sim |  | Genero declarado no cadastro funcional |
| `ds_estado_civil` | character varying(20) | sim |  | Estado civil declarado no cadastro funcional |
| `dt_nascimento` | date | sim |  | Data de nascimento |
| `dt_admissao` | date | sim |  | Data de admissao na empresa |
| `fl_assalariado` | boolean | sim |  | TRUE para regime assalariado; FALSE para horista |
| `fl_vendedor` | boolean | nao |  | TRUE quando o funcionario integra a forca de vendas (Sales.SalesPerson) |
| `vl_cota_vendas` | numeric(19,4) | sim |  | Cota de vendas atribuida; nulo para nao vendedores |
| `vl_bonus` | numeric(19,4) | sim |  | Bonificacao acordada para o vendedor |
| `pc_comissao` | numeric(10,4) | sim |  | Percentual de comissao sobre vendas |
| `hash_scd` | character(32) | nao |  | MD5 dos atributos monitorados |
| `dt_modificacao_origem` | timestamp without time zone | sim |  | ModifiedDate do registro no OLTP |
| `dt_carga` | timestamp without time zone | nao |  | Momento em que a linha foi inserida no DW |
| `dt_atualizacao` | timestamp without time zone | nao |  | Momento da ultima sobrescrita da linha (SCD Tipo 1) |

### `dw.dim_geografia`

Dimensao geografica do endereco de entrega; hierarquia Regiao > Pais > Estado > Cidade

**Linhas carregadas:** 19.615

| Coluna | Tipo | Nulo | Chave | Descricao |
|---|---|---|---|---|
| `sk_geografia` | bigint | nao | PK | Chave substituta da localidade |
| `id_endereco` | integer | nao |  | Chave natural (Person.Address.AddressID) |
| `ds_cidade` | character varying(60) | nao |  | Municipio do endereco |
| `cd_estado` | character varying(5) | sim |  | Sigla do estado ou provincia |
| `nm_estado` | character varying(60) | nao |  | Nome do estado ou provincia |
| `cd_pais` | character(3) | sim |  | Codigo ISO do pais |
| `nm_pais` | character varying(60) | nao |  | Nome do pais |
| `nm_regiao` | character varying(60) | nao |  | Agrupamento continental do territorio associado ao estado |
| `cd_postal` | character varying(15) | sim |  | Codigo postal do endereco |
| `hash_scd` | character(32) | nao |  | MD5 dos atributos monitorados |
| `dt_modificacao_origem` | timestamp without time zone | sim |  | ModifiedDate do registro no OLTP |
| `dt_carga` | timestamp without time zone | nao |  | Momento em que a linha foi inserida no DW |
| `dt_atualizacao` | timestamp without time zone | nao |  | Momento da ultima sobrescrita da linha (SCD Tipo 1) |

### `dw.dim_metodo_envio`

Dimensao conformada de modalidade de frete, compartilhada por vendas e compras

**Linhas carregadas:** 6

| Coluna | Tipo | Nulo | Chave | Descricao |
|---|---|---|---|---|
| `sk_metodo_envio` | bigint | nao | PK | Chave substituta da modalidade de frete |
| `id_metodo_envio` | integer | nao |  | Chave natural (Purchasing.ShipMethod.ShipMethodID) |
| `nm_metodo_envio` | character varying(60) | nao |  | Nome da transportadora ou modalidade de entrega |
| `vl_taxa_base` | numeric(19,4) | sim |  | Taxa fixa cobrada por remessa |
| `vl_taxa_por_peso` | numeric(19,4) | sim |  | Taxa variavel cobrada por unidade de peso |
| `hash_scd` | character(32) | nao |  | MD5 dos atributos monitorados |
| `dt_modificacao_origem` | timestamp without time zone | sim |  | ModifiedDate do registro no OLTP |
| `dt_carga` | timestamp without time zone | nao |  | Momento em que a linha foi inserida no DW |
| `dt_atualizacao` | timestamp without time zone | nao |  | Momento da ultima sobrescrita da linha (SCD Tipo 1) |

### `dw.dim_produto`

Dimensao produto com historico (SCD Tipo 2); hierarquia Categoria > Subcategoria > Modelo > Produto

**Linhas carregadas:** 505

| Coluna | Tipo | Nulo | Chave | Descricao |
|---|---|---|---|---|
| `sk_produto` | bigint | nao | PK | Chave substituta; identifica uma VERSAO do produto, nao o produto |
| `id_produto` | integer | nao |  | Chave natural (Production.Product.ProductID); repete-se entre versoes |
| `cd_produto` | character varying(25) | sim |  | Codigo comercial do produto (ProductNumber) |
| `nm_produto` | character varying(100) | nao |  | Nome comercial do produto |
| `nm_categoria` | character varying(60) | nao |  | Nivel 1 da hierarquia de produto (Bikes, Components, Clothing, Accessories) |
| `nm_subcategoria` | character varying(60) | nao |  | Nivel 2 da hierarquia de produto |
| `nm_modelo` | character varying(60) | nao |  | Nivel 3 da hierarquia: modelo que agrupa variacoes de cor e tamanho |
| `ds_linha` | character varying(30) | nao |  | Linha do produto (Road, Mountain, Touring, Standard) |
| `ds_classe` | character varying(30) | nao |  | Classe de posicionamento (Alta, Media, Baixa) |
| `ds_estilo` | character varying(30) | nao |  | Publico-alvo (Masculino, Feminino, Unissex) |
| `ds_cor` | character varying(30) | nao |  | Cor do produto |
| `ds_tamanho` | character varying(15) | sim |  | Tamanho do produto, na unidade do cadastro de origem |
| `vl_peso` | numeric(12,2) | sim |  | Peso unitario do produto |
| `nm_unidade_peso` | character varying(30) | sim |  | Unidade de medida do peso |
| `vl_custo_padrao` | numeric(19,4) | nao |  | Custo padrao vigente na versao (atributo monitorado pelo SCD Tipo 2) |
| `vl_preco_lista` | numeric(19,4) | nao |  | Preco de tabela vigente na versao (atributo monitorado pelo SCD Tipo 2) |
| `fl_fabricacao_propria` | boolean | nao |  | TRUE para item fabricado internamente; FALSE para item revendido |
| `fl_produto_acabado` | boolean | nao |  | TRUE para produto acabado, vendavel ao cliente final |
| `qt_estoque_seguranca` | integer | sim |  | Estoque minimo de seguranca definido no planejamento |
| `qt_ponto_reposicao` | integer | sim |  | Nivel de estoque que dispara nova reposicao |
| `nr_dias_fabricacao` | integer | sim |  | Prazo de fabricacao em dias |
| `dt_inicio_venda` | date | sim |  | Data de inicio da comercializacao |
| `dt_fim_venda` | date | sim |  | Data de encerramento da comercializacao |
| `dt_descontinuado` | date | sim |  | Data em que o produto foi descontinuado |
| `nr_versao` | integer | nao |  | Numero sequencial da versao do produto (1 = versao original) |
| `dt_inicio_validade` | date | nao |  | Inicio da vigencia da versao; a versao 1 comeca em 1900-01-01 |
| `dt_fim_validade` | date | nao |  | Fim da vigencia da versao; 9999-12-31 na versao corrente |
| `fl_corrente` | boolean | nao |  | TRUE apenas na versao vigente do produto |
| `hash_scd` | character(32) | nao |  | MD5 dos atributos monitorados; alteracao no hash dispara nova versao |
| `dt_modificacao_origem` | timestamp without time zone | sim |  | ModifiedDate do registro no OLTP que originou esta versao |
| `dt_carga` | timestamp without time zone | nao |  | Momento em que a linha foi inserida no DW |
| `dt_atualizacao` | timestamp without time zone | nao |  | Momento da ultima alteracao da linha no DW |

### `dw.dim_promocao`

Dimensao promocao (SCD Tipo 1): oferta aplicada a cada item de venda

**Linhas carregadas:** 17

| Coluna | Tipo | Nulo | Chave | Descricao |
|---|---|---|---|---|
| `sk_promocao` | bigint | nao | PK | Chave substituta da oferta |
| `id_promocao` | integer | nao |  | Chave natural (Sales.SpecialOffer.SpecialOfferID) |
| `ds_promocao` | character varying(255) | nao |  | Descricao comercial da oferta |
| `tp_promocao` | character varying(60) | nao |  | Mecanica da oferta (por volume, sazonal, excedente etc.) |
| `ds_categoria` | character varying(60) | nao |  | Publico da oferta (Reseller ou Customer) |
| `pc_desconto` | numeric(10,4) | nao |  | Percentual de desconto previsto na oferta |
| `qt_minima` | integer | sim |  | Quantidade minima para habilitar a oferta |
| `qt_maxima` | integer | sim |  | Quantidade maxima coberta pela oferta |
| `dt_inicio` | date | sim |  | Inicio da vigencia da oferta |
| `dt_fim` | date | sim |  | Fim da vigencia da oferta |
| `fl_com_desconto` | boolean | nao |  | FALSE para a oferta neutra "No Discount" (id 1), TRUE para promocoes efetivas |
| `hash_scd` | character(32) | nao |  | MD5 dos atributos monitorados |
| `dt_modificacao_origem` | timestamp without time zone | sim |  | ModifiedDate do registro no OLTP |
| `dt_carga` | timestamp without time zone | nao |  | Momento em que a linha foi inserida no DW |
| `dt_atualizacao` | timestamp without time zone | nao |  | Momento da ultima sobrescrita da linha (SCD Tipo 1) |

### `dw.dim_status_pedido`

Dimensao estatica de situacao do pedido, compartilhada por vendas e compras

**Linhas carregadas:** 11

| Coluna | Tipo | Nulo | Chave | Descricao |
|---|---|---|---|---|
| `sk_status` | integer | nao | PK | Chave substituta da situacao |
| `cd_status` | smallint | nao |  | Codigo numerico da situacao no sistema de origem |
| `ds_dominio` | character varying(10) | nao |  | VENDA ou COMPRA - o mesmo codigo numerico tem significados distintos em cada processo |
| `nm_status` | character varying(40) | nao |  | Descricao da situacao em portugues |
| `fl_concluido` | boolean | nao |  | TRUE quando a situacao representa um ciclo concluido com sucesso |
| `fl_cancelado` | boolean | nao |  | TRUE quando a situacao representa cancelamento ou rejeicao |

### `dw.dim_tempo`

Dimensao calendario diaria; SK inteligente no formato AAAAMMDD

**Linhas carregadas:** 1.462

| Coluna | Tipo | Nulo | Chave | Descricao |
|---|---|---|---|---|
| `sk_tempo` | integer | nao | PK | Chave substituta no formato AAAAMMDD (ex.: 20130715). -1 = Nao Informado |
| `dt_data` | date | nao |  | Data do calendario (chave natural da dimensao) |
| `nr_ano` | smallint | nao |  | Ano com quatro digitos |
| `nr_semestre` | smallint | nao |  | Semestre do ano (1 ou 2) |
| `nr_trimestre` | smallint | nao |  | Trimestre do ano (1 a 4) |
| `nr_mes` | smallint | nao |  | Mes do ano (1 a 12) |
| `nr_dia` | smallint | nao |  | Dia do mes (1 a 31) |
| `nr_semana_ano` | smallint | nao |  | Semana ISO do ano (1 a 53) |
| `nr_dia_semana` | smallint | nao |  | Dia da semana (1 = segunda-feira a 7 = domingo) |
| `nr_dia_ano` | smallint | nao |  | Dia sequencial dentro do ano (1 a 366) |
| `nm_mes` | character varying(15) | nao |  | Nome do mes por extenso, em portugues |
| `nm_mes_abrev` | character varying(3) | nao |  | Abreviacao do nome do mes (tres letras) |
| `nm_dia_semana` | character varying(15) | nao |  | Nome do dia da semana por extenso, em portugues |
| `ds_ano_mes` | character(7) | nao |  | Competencia no formato AAAA-MM, para ordenacao cronologica em relatorios |
| `ds_ano_trimestre` | character(7) | nao |  | Trimestre no formato AAAA-Qn |
| `fl_fim_semana` | boolean | nao |  | Indica se a data cai em sabado ou domingo |
| `dt_primeiro_dia_mes` | date | nao |  | Primeiro dia do mes da data, para agregacoes mensais |
| `dt_ultimo_dia_mes` | date | nao |  | Ultimo dia do mes da data, para calculos de fechamento |

### `dw.dim_territorio`

Dimensao territorio de vendas; hierarquia Grupo (continente) > Pais > Territorio

**Linhas carregadas:** 11

| Coluna | Tipo | Nulo | Chave | Descricao |
|---|---|---|---|---|
| `sk_territorio` | bigint | nao | PK | Chave substituta do territorio |
| `id_territorio` | integer | nao |  | Chave natural (Sales.SalesTerritory.TerritoryID) |
| `nm_territorio` | character varying(60) | nao |  | Nome do territorio comercial |
| `nm_grupo` | character varying(60) | nao |  | Agrupamento continental do territorio (North America, Europe, Pacific) |
| `cd_pais` | character(3) | sim |  | Codigo ISO do pais do territorio |
| `nm_pais` | character varying(60) | sim |  | Nome do pais do territorio |
| `vl_vendas_ano_atual` | numeric(19,4) | sim |  | Vendas acumuladas no ano corrente, conforme o cadastro de origem |
| `vl_vendas_ano_ante` | numeric(19,4) | sim |  | Vendas do ano anterior, conforme o cadastro de origem |
| `vl_custo_ano_atual` | numeric(19,4) | sim |  | Custo acumulado no ano corrente, conforme o cadastro de origem |
| `hash_scd` | character(32) | nao |  | MD5 dos atributos monitorados |
| `dt_modificacao_origem` | timestamp without time zone | sim |  | ModifiedDate do registro no OLTP |
| `dt_carga` | timestamp without time zone | nao |  | Momento em que a linha foi inserida no DW |
| `dt_atualizacao` | timestamp without time zone | nao |  | Momento da ultima sobrescrita da linha (SCD Tipo 1) |


## Metadados de controle (`meta`)

### `meta.etl_controle`

Marca d'agua por entidade: base da estrategia de carga incremental

**Linhas carregadas:** 10

| Coluna | Tipo | Nulo | Chave | Descricao |
|---|---|---|---|---|
| `nm_entidade` | character varying(60) | nao | PK | Entidade do DW a que a marca d'agua se refere |
| `ds_tabela_origem` | character varying(120) | nao |  | Tabela do OLTP que alimenta a entidade |
| `ds_coluna_controle` | character varying(60) | nao |  | Coluna de auditoria usada como criterio de incremento |
| `dt_ultima_carga` | timestamp without time zone | nao |  | Maior ModifiedDate ja processado com sucesso para a entidade |
| `qt_registros_ultima` | bigint | nao |  | Volume de registros movimentados na ultima execucao |
| `qt_registros_total` | bigint | nao |  | Volume acumulado de registros processados desde a implantacao |
| `dt_atualizacao` | timestamp without time zone | nao |  | Momento da ultima atualizacao da marca d'agua |

### `meta.etl_execucao`

Log de auditoria das execucoes da ETL (rastreabilidade e reprocessamento)

**Linhas carregadas:** 10

| Coluna | Tipo | Nulo | Chave | Descricao |
|---|---|---|---|---|
| `id_execucao` | bigint | nao | PK | Identificador sequencial da linha de log |
| `id_lote` | character varying(250) | nao |  | run_id do Airflow: liga cada linha de log a execucao da DAG |
| `nm_entidade` | character varying(60) | nao |  | Entidade processada nesta linha de log |
| `ds_fase` | character varying(20) | nao |  | DIMENSAO ou FATO |
| `dt_inicio` | timestamp without time zone | nao |  | Inicio do processamento da entidade |
| `dt_fim` | timestamp without time zone | sim |  | Termino do processamento da entidade |
| `qt_extraidos` | bigint | sim |  | Registros trazidos do OLTP na janela incremental |
| `qt_inseridos` | bigint | sim |  | Registros novos gravados no DW |
| `qt_atualizados` | bigint | sim |  | Registros existentes efetivamente alterados no DW |
| `ds_marca_agua_de` | timestamp without time zone | sim |  | Limite inferior da janela processada |
| `ds_marca_agua_ate` | timestamp without time zone | sim |  | Maior ModifiedDate observado no lote; nova marca d'agua |
| `ds_status` | character varying(20) | nao |  | EM_EXECUCAO, SUCESSO, SEM_ALTERACAO ou ERRO |
| `ds_mensagem` | text | sim |  | Detalhe do erro, quando houver |

### `meta.etl_validacao`

Conferencia OLTP x DW e testes de integridade de cada ciclo de ETL

**Linhas carregadas:** 15

| Coluna | Tipo | Nulo | Chave | Descricao |
|---|---|---|---|---|
| `id_validacao` | bigint | nao | PK |  |
| `id_lote` | character varying(250) | nao |  | run_id do Airflow que executou a verificacao |
| `ds_verificacao` | character varying(120) | nao |  | Descricao da verificacao realizada |
| `vl_origem` | numeric(19,4) | sim |  | Valor apurado no OLTP ou valor esperado |
| `vl_destino` | numeric(19,4) | sim |  | Valor apurado no Data Warehouse |
| `fl_aprovado` | boolean | nao |  | TRUE quando a verificacao foi aprovada |
| `dt_verificacao` | timestamp without time zone | nao |  | Momento da verificacao |
