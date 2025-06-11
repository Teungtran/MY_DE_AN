USE CUSTOMER_SERVICE;
GO

CREATE TRIGGER trg_InsertOrder_UpdatePriceAndInventory
ON [Order]
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;

    -- Update total price in [Order]
    UPDATE o
    SET o.price = i.price * ins.quantity
    FROM [Order] o
    JOIN inserted ins ON o.order_id = ins.order_id
    JOIN Item i ON i.device_name = ins.device_name;

    -- Update inventory in Item table
    UPDATE i
    SET i.in_store = i.in_store - ins.quantity
    FROM Item i
    JOIN inserted ins ON i.device_name = ins.device_name;
END;
