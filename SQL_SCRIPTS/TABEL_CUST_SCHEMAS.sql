-- Drop tables in the correct order due to FK dependencies
DROP TABLE IF EXISTS ticket;
DROP TABLE IF EXISTS Booking;
DROP TABLE IF EXISTS [Order];
DROP TABLE IF EXISTS Item;
DROP TABLE IF EXISTS Customer_info;

-- Create Customer_info table
CREATE TABLE Customer_info (
    user_id NVARCHAR(50) PRIMARY KEY,
    customer_name NVARCHAR(100) NOT NULL,
    address NVARCHAR(255),
    preferences NVARCHAR(255),
    age INT,
    customer_phone NVARCHAR(20) UNIQUE,
    password NVARCHAR(255) NOT NULL
);

-- Create Item table
CREATE TABLE Item (
    item_id INT PRIMARY KEY IDENTITY(1,1),
    device_name NVARCHAR(100) UNIQUE NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    category NVARCHAR(50),
    in_store INT
);

-- Create Order table
CREATE TABLE [Order] (
    order_id NVARCHAR(20) PRIMARY KEY,
    device_name NVARCHAR(100) NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    price DECIMAL(18,2) NOT NULL DEFAULT 0,
    payment NVARCHAR(50) DEFAULT 'cash on delivery',
    shipping BIT DEFAULT 1,
    time_reservation DATETIME,
    address NVARCHAR(255),
    customer_phone NVARCHAR(20),
    customer_name NVARCHAR(100),
    status NVARCHAR(20) CHECK (status IN ('Processing', 'Shipped', 'Canceled', 'Returned', 'Received')),
    user_id NVARCHAR(50),
    FOREIGN KEY (device_name) REFERENCES Item(device_name),
    FOREIGN KEY (user_id) REFERENCES Customer_info(user_id)
);

-- Create Booking table
CREATE TABLE Booking (
    booking_id NVARCHAR(20) PRIMARY KEY,
    customer_name NVARCHAR(100),
    customer_phone NVARCHAR(20),
    reason NVARCHAR(255) NOT NULL,
    time DATETIME NOT NULL,
    note NVARCHAR(255),
    status NVARCHAR(20) CHECK (status IN ('Scheduled', 'Canceled', 'Finished')),
    user_id NVARCHAR(50),
    FOREIGN KEY (user_id) REFERENCES Customer_info(user_id)
);

-- Create Ticket table
CREATE TABLE ticket (
    ticket_id NVARCHAR(50) PRIMARY KEY,
    content NVARCHAR(MAX),
    description NVARCHAR(MAX),
    customer_name NVARCHAR(100),
    customer_phone NVARCHAR(20),
    time DATETIME,
    status NVARCHAR(20) CHECK (status IN ('Pending', 'Resolving', 'Canceled', 'Finished')),
    user_id NVARCHAR(50),
    FOREIGN KEY (user_id) REFERENCES Customer_info(user_id)
);
use CUSTOMER_SERVICE
go
ALTER TABLE Customer_info
ALTER COLUMN preferences NVARCHAR(MAX);