use CUSTOMER_SERVICE
go
select * from Customer_info


CREATE TABLE ticket (
    ticket_id NVARCHAR(50) PRIMARY KEY,
    content NVARCHAR(MAX),
    description NVARCHAR(MAX),
    customer_name NVARCHAR(100),
    customer_phone NVARCHAR(20),
    time DATETIME,
    status NVARCHAR(20) CHECK (status IN ('Pending', 'Resolving', 'Canceled', 'Finished'))
);
ALTER TABLE [Order]
ADD price DECIMAL(10, 2);
