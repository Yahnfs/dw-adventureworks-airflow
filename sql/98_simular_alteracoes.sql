-- =============================================================================
-- SIMULACAO DE MOVIMENTO NO OLTP (executado no SQL Server)
--
-- Comprova que a ETL e incremental. Executado pela DAG simular_movimento_oltp,
-- provoca na origem os cinco eventos que a carga precisa reconhecer:
--
--   (A) preco de produto alterado    -> nova versao em dim_produto (SCD Tipo 2)
--   (B) cadastro de fornecedor       -> sobrescrita em dim_fornecedor (SCD Tipo 1)
--   (C) nome do cliente em Person    -> dim_cliente, por tabela secundaria
--   (D) cabecalho de pedido antigo   -> atualiza as linhas do pedido na fato
--   (E) pedido novo com dois itens   -> duas linhas novas em fato_vendas
--
-- ATENCAO: este script ESCREVE no banco de origem. Serve apenas a base de
-- demonstracao AdventureWorks.
-- =============================================================================

SET NOCOUNT ON;
GO

-- (A) Reajuste de 10% no preco de lista do produto 707.
UPDATE Production.Product
   SET ListPrice    = ListPrice * 1.10,
       ModifiedDate = SYSDATETIME()
 WHERE ProductID = 707;
GO

-- (B) Alternancia do nivel de credito do fornecedor 1492.
UPDATE Purchasing.Vendor
   SET CreditRating = CASE WHEN CreditRating = 1 THEN 2 ELSE 1 END,
       ModifiedDate = SYSDATETIME()
 WHERE BusinessEntityID = 1492;
GO

-- (C) Alteracao do sobrenome do cliente 11000. A linha de Sales.Customer nao e
-- tocada: a mudanca so e vista porque a extracao observa tambem Person.Person.
UPDATE p
   SET p.LastName = CASE WHEN p.LastName LIKE '% Jr' THEN LEFT(p.LastName, LEN(p.LastName) - 3)
                         ELSE p.LastName + ' Jr' END,
       p.ModifiedDate = SYSDATETIME()
  FROM Person.Person AS p
  JOIN Sales.Customer AS c ON c.PersonID = p.BusinessEntityID
 WHERE c.CustomerID = 11000;
GO

-- (D) Data de envio do pedido 43659 adiada em um dia. Altera so o cabecalho, e
-- as linhas de detalhe permanecem com a ModifiedDate antiga.
UPDATE Sales.SalesOrderHeader
   SET ShipDate     = DATEADD(day, 1, ShipDate),
       ModifiedDate = SYSDATETIME()
 WHERE SalesOrderID = 43659;
GO

-- (E) Pedido novo com dois itens.
BEGIN TRANSACTION;

DECLARE @SalesOrderID int;

INSERT INTO Sales.SalesOrderHeader
    (RevisionNumber, OrderDate, DueDate, ShipDate, Status, OnlineOrderFlag,
     CustomerID, SalesPersonID, TerritoryID, BillToAddressID, ShipToAddressID,
     ShipMethodID, SubTotal, TaxAmt, Freight, ModifiedDate)
VALUES
    (1, SYSDATETIME(), DATEADD(day, 7, SYSDATETIME()), DATEADD(day, 3, SYSDATETIME()),
     5, 0, 29825, 279, 5, 985, 985, 5, 0, 0, 0, SYSDATETIME());

SET @SalesOrderID = SCOPE_IDENTITY();

INSERT INTO Sales.SalesOrderDetail
    (SalesOrderID, OrderQty, ProductID, SpecialOfferID, UnitPrice,
     UnitPriceDiscount, ModifiedDate)
VALUES
    (@SalesOrderID, 3, 707, 1, 34.99, 0.00, SYSDATETIME()),
    (@SalesOrderID, 2, 708, 1, 34.99, 0.10, SYSDATETIME());

-- Recalcula o subtotal para manter consistente o rateio de frete e imposto.
UPDATE h
   SET h.SubTotal     = d.Subtotal,
       h.Freight      = ROUND(d.Subtotal * 0.025, 4),
       h.TaxAmt       = ROUND(d.Subtotal * 0.080, 4),
       h.ModifiedDate = SYSDATETIME()
  FROM Sales.SalesOrderHeader AS h
 CROSS APPLY (
     SELECT SUM(LineTotal) AS Subtotal
       FROM Sales.SalesOrderDetail
      WHERE SalesOrderID = @SalesOrderID
 ) AS d
 WHERE h.SalesOrderID = @SalesOrderID;

COMMIT TRANSACTION;
GO
