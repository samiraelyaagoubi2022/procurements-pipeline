-- ============================================================================
-- METASTORE HIVE/TRINO POUR PROCUREMENT
-- ============================================================================

-- 1. Créer la base de données Hive pour le procurement
CREATE DATABASE IF NOT EXISTS procurement_hdfs
COMMENT 'Base de données Hive pour le pipeline de procurement';

USE procurement_hdfs;

-- 2. Table externe pour les commandes (format JSON)
CREATE EXTERNAL TABLE IF NOT EXISTS raw_orders (
    order_id STRING,
    store_id STRING,
    order_date STRING,
    items ARRAY<STRUCT<
        sku: STRING,
        product_name: STRING,
        quantity: INT,
        unit_price: DOUBLE
    >>
)
PARTITIONED BY (order_date_part STRING)
ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'
STORED AS TEXTFILE
LOCATION 'hdfs://namenode:9000/raw/orders/'
TBLPROPERTIES (
    'skip.header.line.count'='0',
    'serialization.format'='1'
);

-- 3. Table externe pour les stocks (format CSV)
CREATE EXTERNAL TABLE IF NOT EXISTS raw_stock (
    snapshot_date STRING,
    warehouse_id STRING,
    sku STRING,
    available_qty INT,
    reserved_qty INT
)
PARTITIONED BY (snapshot_date_part STRING)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 'hdfs://namenode:9000/raw/stock/'
TBLPROPERTIES (
    'skip.header.line.count'='1',
    'serialization.format'='1'
);

-- 4. Table pour les données agrégées quotidiennes
CREATE EXTERNAL TABLE IF NOT EXISTS aggregated_orders (
    aggregation_date STRING,
    sku STRING,
    total_quantity INT,
    num_orders INT,
    num_stores INT,
    avg_quantity_per_order DOUBLE,
    total_value DOUBLE
)
PARTITIONED BY (aggregation_date_part STRING)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 'hdfs://namenode:9000/processed/aggregated_orders/'
TBLPROPERTIES (
    'skip.header.line.count'='1',
    'serialization.format'='1'
);

-- 5. Table pour la demande nette
CREATE EXTERNAL TABLE IF NOT EXISTS net_demand (
    calculation_date STRING,
    sku STRING,
    product_name STRING,
    category STRING,
    supplier_id STRING,
    daily_demand INT,
    current_stock INT,
    safety_stock_qty INT,
    net_demand INT,
    rounded_demand INT,
    final_order_qty INT,
    unit_price DOUBLE,
    order_value DOUBLE
)
PARTITIONED BY (calculation_date_part STRING)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 'hdfs://namenode:9000/processed/net_demand/'
TBLPROPERTIES (
    'skip.header.line.count'='1',
    'serialization.format'='1'
);

-- 6. Fonctions utilitaires
CREATE FUNCTION IF NOT EXISTS add_partitions AS 'org.apache.hadoop.hive.ql.udf.generic.GenericUDFAddPartitions';

-- 7. Vues pour faciliter l'accès
CREATE VIEW IF NOT EXISTS vw_orders_today AS
SELECT * FROM raw_orders 
WHERE order_date_part = DATE_FORMAT(CURRENT_DATE, 'yyyy-MM-dd');

CREATE VIEW IF NOT EXISTS vw_stock_today AS
SELECT * FROM raw_stock 
WHERE snapshot_date_part = DATE_FORMAT(CURRENT_DATE, 'yyyy-MM-dd');

-- 8. Vérification
SHOW TABLES;
DESCRIBE raw_orders;
DESCRIBE raw_stock;