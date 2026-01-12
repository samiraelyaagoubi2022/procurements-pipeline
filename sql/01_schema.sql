-- ============================================
-- 01_SCHEMA.SQL - Creation des tables
-- Version corrigée avec safety_stock_qty
-- ============================================

DROP TABLE IF EXISTS safety_stocks CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS suppliers CASCADE;
DROP TABLE IF EXISTS warehouses CASCADE;

CREATE TABLE suppliers (
    supplier_id VARCHAR(50) PRIMARY KEY,
    supplier_name VARCHAR(200) NOT NULL,
    contact_email VARCHAR(100),
    contact_phone VARCHAR(20),
    lead_time_days INT NOT NULL DEFAULT 2,
    min_order_value DECIMAL(10,2) DEFAULT 0.00,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE warehouses (
    warehouse_id VARCHAR(50) PRIMARY KEY,
    warehouse_name VARCHAR(200) NOT NULL,
    city VARCHAR(100) NOT NULL,
    region VARCHAR(100),
    address TEXT,
    capacity_m3 DECIMAL(10,2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE products (
    sku VARCHAR(50) PRIMARY KEY,
    product_name VARCHAR(200) NOT NULL,
    category VARCHAR(100) NOT NULL,
    supplier_id VARCHAR(50) NOT NULL REFERENCES suppliers(supplier_id),
    unit_price DECIMAL(10,2) NOT NULL,
    pack_size INT NOT NULL DEFAULT 1,
    moq INT NOT NULL DEFAULT 1,
    unit_of_measure VARCHAR(20) DEFAULT 'piece',
    safety_stock_qty INT NOT NULL DEFAULT 100,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE safety_stocks (
    sku VARCHAR(50) NOT NULL REFERENCES products(sku),
    warehouse_id VARCHAR(50) NOT NULL REFERENCES warehouses(warehouse_id),
    safety_stock_qty INT NOT NULL DEFAULT 0,
    reorder_point INT,
    max_stock_qty INT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (sku, warehouse_id)
);

CREATE INDEX idx_products_supplier ON products(supplier_id);
CREATE INDEX idx_products_category ON products(category);

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO procurement_user;