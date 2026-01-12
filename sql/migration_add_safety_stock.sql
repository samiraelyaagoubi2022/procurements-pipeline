-- ============================================
-- MIGRATION: Ajouter safety_stock_qty à products
-- ============================================

-- 1. Ajouter la colonne si elle n'existe pas
ALTER TABLE products 
ADD COLUMN IF NOT EXISTS safety_stock_qty INTEGER DEFAULT 100;

-- 2. Mettre à jour les valeurs selon la catégorie
UPDATE products SET safety_stock_qty = CASE 
    WHEN category = 'PRODUITS_LAITIERS' THEN 100
    WHEN category = 'BISCUITERIE' THEN 200
    WHEN category = 'EPICERIE' THEN 150
    WHEN category = 'CONSERVES' THEN 300
    WHEN category = 'BOISSONS' THEN 120
    WHEN category = 'HYGIENE' THEN 180
    WHEN category = 'CONFISERIE' THEN 150
    ELSE 100
END;

-- 3. Ajouter le fournisseur SUP_001 s'il n'existe pas
INSERT INTO suppliers (supplier_id, supplier_name, contact_email, contact_phone, lead_time_days, min_order_value, is_active)
VALUES ('SUP_001', 'Fournisseur Général Maroc', 'contact@fgm.ma', '+212522123456', 2, 5000.00, TRUE)
ON CONFLICT (supplier_id) DO NOTHING;

-- 4. S'assurer que SUP-001 existe aussi (avec tiret)
INSERT INTO suppliers (supplier_id, supplier_name, contact_email, contact_phone, lead_time_days, min_order_value, is_active)
VALUES ('SUP-001', 'Centrale Laitière', 'commandes@centralelaitiere.ma', '+212 522 334 455', 1, 5000.00, TRUE)
ON CONFLICT (supplier_id) DO NOTHING;

-- 5. Vérification
SELECT 'Migration terminée' AS status;
SELECT 'Produits avec safety_stock_qty:' AS info, COUNT(*) AS count 
FROM products WHERE safety_stock_qty IS NOT NULL;
SELECT 'Fournisseurs disponibles:' AS info, COUNT(*) AS count FROM suppliers;
SELECT supplier_id, supplier_name FROM suppliers ORDER BY supplier_id;