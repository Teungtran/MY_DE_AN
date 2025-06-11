use CUSTOMER_SERVICE
go
CREATE TABLE Customer_info (
    user_id INT PRIMARY KEY IDENTITY(1,1),
    customer_name NVARCHAR(100) NOT NULL,
    address NVARCHAR(255),
    preferences NVARCHAR(255),
    age INT,
    customer_phone NVARCHAR(20) UNIQUE,
    password NVARCHAR(255) NOT NULL
);

-- Table 2: Item
CREATE TABLE Item (
    item_id INT PRIMARY KEY IDENTITY(1,1),
    device_name NVARCHAR(100) UNIQUE NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    category NVARCHAR(50),
    in_store INT
);

-- Table 3: [Order]
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
    user_id INT NULL,
    FOREIGN KEY (user_id) REFERENCES Customer_info(user_id),
    FOREIGN KEY (device_name) REFERENCES Item(device_name),
    FOREIGN KEY (customer_phone) REFERENCES Customer_info(customer_phone)
);

-- Table 4: Booking
CREATE TABLE Booking (
    booking_id NVARCHAR(20) PRIMARY KEY,
    customer_name NVARCHAR(100),
    customer_phone NVARCHAR(20),
    reason NVARCHAR(255) NOT NULL,
    time DATETIME NOT NULL,
    note NVARCHAR(255),
    status NVARCHAR(20) CHECK (status IN ('Scheduled', 'Canceled', 'Finished')),
    FOREIGN KEY (customer_phone) REFERENCES Customer_info(customer_phone)
);

-- Table 5: Ticket
CREATE TABLE ticket (
    ticket_id NVARCHAR(50) PRIMARY KEY,
    content NVARCHAR(MAX),
    description NVARCHAR(MAX),
    customer_name NVARCHAR(100),
    customer_phone NVARCHAR(20),
    time DATETIME,
    status NVARCHAR(20) CHECK (status IN ('Pending', 'Resolving', 'Canceled', 'Finished')),
    FOREIGN KEY (customer_phone) REFERENCES Customer_info(customer_phone)
);