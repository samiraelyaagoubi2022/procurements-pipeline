-- ============================================
-- 02_MASTER_DATA.SQL
-- Données maîtres pour la région de Casablanca
-- ============================================

-- Nettoyage préalable
DELETE FROM safety_stocks;
DELETE FROM products;
DELETE FROM suppliers;
DELETE FROM warehouses;

-- ============================================
-- 1. FOURNISSEURS MAROCAINS (15)
-- ============================================
INSERT INTO suppliers (supplier_id, supplier_name, contact_email, contact_phone, lead_time_days, min_order_value, is_active) VALUES
('SUP-001', 'Centrale Laitière', 'commandes@centralelaitiere.ma', '+212 522 334 455', 1, 5000.00, TRUE),
('SUP-002', 'Bimo', 'orders@bimo.ma', '+212 522 445 566', 1, 3000.00, TRUE),
('SUP-003', 'Lesieur Cristal', 'achat@lesieur.ma', '+212 522 556 677', 2, 8000.00, TRUE),
('SUP-004', 'Cosumar', 'commandes@cosumar.ma', '+212 522 667 788', 2, 10000.00, TRUE),
('SUP-005', 'Dari Couspate', 'orders@dari.ma', '+212 522 778 899', 1, 4000.00, TRUE),
('SUP-006', 'SBM Coca-Cola', 'service@cocacola.ma', '+212 522 889 900', 1, 6000.00, TRUE),
('SUP-007', 'Oulmès', 'commandes@oulmes.ma', '+212 522 990 011', 1, 3500.00, TRUE),
('SUP-008', 'Unilever Maghreb', 'orders@unilever.ma', '+212 522 101 122', 2, 7000.00, TRUE),
('SUP-009', 'Nestlé Maroc', 'achats@nestle.ma', '+212 522 212 233', 2, 9000.00, TRUE),
('SUP-010', 'Bel Maroc', 'commandes@bel.ma', '+212 522 323 344', 1, 4500.00, TRUE),
('SUP-011', 'Agropur', 'orders@agropur.ma', '+212 522 434 455', 1, 3000.00, TRUE),
('SUP-012', 'Savola Maroc', 'service@savola.ma', '+212 522 545 566', 2, 6500.00, TRUE),
('SUP-013', 'Colgate Palmolive', 'orders@colgate.ma', '+212 522 656 677', 2, 5500.00, TRUE),
('SUP-014', 'Procter & Gamble Maroc', 'commandes@pg.ma', '+212 522 767 788', 2, 8500.00, TRUE),
('SUP-015', 'Maroc Distribution', 'service@marocdist.ma', '+212 522 878 899', 1, 2500.00, TRUE);

-- ============================================
-- 2. ENTREPÔTS CASABLANCA (2)
-- ============================================
INSERT INTO warehouses (warehouse_id, warehouse_name, city, address, capacity_m3, is_active) VALUES
('WH-CASA-01', 'Entrepôt Central Aïn Sebaâ', 'Casablanca', 'Zone Industrielle Aïn Sebaâ, Rue 15', 15000.00, TRUE),
('WH-CASA-02', 'Entrepôt Frais Sidi Moumen', 'Casablanca', 'Quartier Industriel Sidi Moumen, Avenue 8', 8000.00, TRUE);

-- ============================================
-- 3. PRODUITS ALIMENTAIRES MAROC (41)
-- ============================================

-- PRODUITS LAITIERS (Centrale Laitière + Bel + Agropur)
INSERT INTO products (sku, product_name, category, supplier_id, unit_price, pack_size, moq, unit_of_measure, is_active) VALUES
('LAIT-001', 'Centrale Lait Entier 1L', 'PRODUITS_LAITIERS', 'SUP-001', 8.50, 6, 60, 'litre', TRUE),
('LAIT-002', 'Centrale Lait Demi-Écrémé 1L', 'PRODUITS_LAITIERS', 'SUP-001', 8.00, 6, 60, 'litre', TRUE),
('YAOURT-001', 'Raibi Jamila Nature 1L', 'PRODUITS_LAITIERS', 'SUP-001', 12.00, 6, 48, 'litre', TRUE),
('FROMAGE-001', 'La Vache Qui Rit 8 portions', 'PRODUITS_LAITIERS', 'SUP-010', 15.00, 12, 72, 'boîte', TRUE),
('BEURRE-001', 'Beurre Le Berger 250g', 'PRODUITS_LAITIERS', 'SUP-011', 22.00, 20, 100, 'plaquette', TRUE),

-- BISCUITS (Bimo)
('BISC-001', 'Bimo Maryse Chocolat 100g', 'BISCUITERIE', 'SUP-002', 4.50, 24, 144, 'paquet', TRUE),
('BISC-002', 'Bimo Sésame 200g', 'BISCUITERIE', 'SUP-002', 7.00, 20, 120, 'paquet', TRUE),
('BISC-003', 'Bimo Gaufrettes 125g', 'BISCUITERIE', 'SUP-002', 5.50, 24, 144, 'paquet', TRUE),

-- HUILES ET CONSERVES (Lesieur)
('HUILE-001', 'Lesieur Cristal Huile 1L', 'EPICERIE', 'SUP-003', 28.00, 12, 72, 'bouteille', TRUE),
('HUILE-002', 'Lesieur Olive Extra 1L', 'EPICERIE', 'SUP-003', 85.00, 6, 36, 'bouteille', TRUE),
('CONS-001', 'Lesieur Sardines 125g', 'CONSERVES', 'SUP-003', 8.50, 50, 250, 'boîte', TRUE),

-- SUCRE (Cosumar)
('SUCRE-001', 'Cosumar Sucre Blanc 1kg', 'EPICERIE', 'SUP-004', 9.00, 20, 100, 'kg', TRUE),
('SUCRE-002', 'Cosumar Morceaux 1kg', 'EPICERIE', 'SUP-004', 10.00, 20, 100, 'kg', TRUE),

-- PÂTES ET COUSCOUS (Dari)
('PATES-001', 'Dari Couscous Fin 1kg', 'EPICERIE', 'SUP-005', 11.00, 10, 50, 'kg', TRUE),
('PATES-002', 'Dari Vermicelles 500g', 'EPICERIE', 'SUP-005', 6.50, 20, 100, 'paquet', TRUE),
('PATES-003', 'Dari Pâtes Macaroni 500g', 'EPICERIE', 'SUP-005', 7.00, 20, 100, 'paquet', TRUE),

-- BOISSONS (SBM Coca-Cola + Oulmès)
('SODA-001', 'Coca-Cola 1.5L', 'BOISSONS', 'SUP-006', 12.00, 6, 48, 'bouteille', TRUE),
('SODA-002', 'Fanta Orange 1.5L', 'BOISSONS', 'SUP-006', 11.00, 6, 48, 'bouteille', TRUE),
('SODA-003', 'Sprite 1.5L', 'BOISSONS', 'SUP-006', 11.00, 6, 48, 'bouteille', TRUE),
('EAU-001', 'Oulmès Eau Plate 1.5L', 'BOISSONS', 'SUP-007', 5.00, 6, 60, 'bouteille', TRUE),
('EAU-002', 'Oulmès Gazeuse 1L', 'BOISSONS', 'SUP-007', 6.50, 12, 72, 'bouteille', TRUE),

-- HYGIENE (Unilever + Colgate + P&G)
('SAV-001', 'Dove Savon 100g', 'HYGIENE', 'SUP-008', 8.00, 48, 240, 'pièce', TRUE),
('SHAM-001', 'Clear Shampooing 400ml', 'HYGIENE', 'SUP-008', 35.00, 12, 60, 'bouteille', TRUE),
('DENT-001', 'Signal Dentifrice 75ml', 'HYGIENE', 'SUP-013', 18.00, 12, 72, 'tube', TRUE),
('LESS-001', 'Ariel Lessive Poudre 3kg', 'HYGIENE', 'SUP-014', 95.00, 4, 24, 'boîte', TRUE),

-- CHOCOLAT ET CONFISERIE (Nestlé)
('CHOC-001', 'Nestlé Dessert 200g', 'CONFISERIE', 'SUP-009', 32.00, 20, 100, 'tablette', TRUE),
('CHOC-002', 'KitKat 4 Fingers 41.5g', 'CONFISERIE', 'SUP-009', 6.00, 36, 180, 'barre', TRUE),
('CAFE-001', 'Nescafé Classic 100g', 'EPICERIE', 'SUP-009', 45.00, 12, 60, 'pot', TRUE),

-- HUILE ET RIZ (Savola)
('HUILE-003', 'Afia Huile Tournesol 2L', 'EPICERIE', 'SUP-012', 48.00, 6, 36, 'bouteille', TRUE),
('RIZ-001', 'Taureau Ailé Riz 1kg', 'EPICERIE', 'SUP-012', 14.00, 10, 50, 'kg', TRUE),

-- PRODUITS DIVERS (Maroc Distribution)
('THE-001', 'Thé Sultan 200g', 'EPICERIE', 'SUP-015', 18.00, 20, 100, 'paquet', TRUE),
('CONF-001', 'Confiture Aïcha 450g', 'EPICERIE', 'SUP-015', 22.00, 12, 72, 'pot', TRUE),
('VIN-001', 'Vinaigre Cristal 1L', 'EPICERIE', 'SUP-015', 9.00, 12, 72, 'bouteille', TRUE),
('SEL-001', 'Sel Fin 1kg', 'EPICERIE', 'SUP-015', 4.00, 20, 100, 'kg', TRUE),
('TOMATE-001', 'Concentré Tomate 400g', 'CONSERVES', 'SUP-015', 12.00, 24, 144, 'boîte', TRUE),
('MIEL-001', 'Miel d''Oranger 500g', 'EPICERIE', 'SUP-015', 65.00, 12, 60, 'pot', TRUE),
('OLIVE-001', 'Olives Vertes 500g', 'CONSERVES', 'SUP-015', 18.00, 12, 72, 'bocal', TRUE),
('HARISSA-001', 'Harissa Cap Bon 200g', 'EPICERIE', 'SUP-015', 8.50, 24, 144, 'tube', TRUE),
('SARDINE-001', 'Sardines Marocaines 125g', 'CONSERVES', 'SUP-015', 9.00, 48, 240, 'boîte', TRUE);

-- ============================================
-- 4. STOCKS DE SÉCURITÉ PAR ENTREPÔT
-- ============================================

-- Entrepôt Central Aïn Sebaâ (WH-CASA-01) - Produits secs
INSERT INTO safety_stocks (sku, warehouse_id, safety_stock_qty, reorder_point, max_stock_qty) VALUES
-- Produits laitiers
('LAIT-001', 'WH-CASA-01', 120, 180, 600),
('LAIT-002', 'WH-CASA-01', 100, 150, 500),
('YAOURT-001', 'WH-CASA-01', 80, 120, 400),
('FROMAGE-001', 'WH-CASA-01', 150, 220, 800),
('BEURRE-001', 'WH-CASA-01', 200, 300, 1000),

-- Biscuits
('BISC-001', 'WH-CASA-01', 300, 450, 1500),
('BISC-002', 'WH-CASA-01', 250, 380, 1200),
('BISC-003', 'WH-CASA-01', 280, 420, 1400),

-- Huiles et conserves
('HUILE-001', 'WH-CASA-01', 150, 220, 800),
('HUILE-002', 'WH-CASA-01', 80, 120, 400),
('CONS-001', 'WH-CASA-01', 500, 750, 2500),
('HUILE-003', 'WH-CASA-01', 100, 150, 600),

-- Sucre
('SUCRE-001', 'WH-CASA-01', 200, 300, 1000),
('SUCRE-002', 'WH-CASA-01', 180, 270, 900),

-- Pâtes et couscous
('PATES-001', 'WH-CASA-01', 100, 150, 600),
('PATES-002', 'WH-CASA-01', 200, 300, 1000),
('PATES-003', 'WH-CASA-01', 180, 270, 900),

-- Boissons
('SODA-001', 'WH-CASA-01', 100, 150, 600),
('SODA-002', 'WH-CASA-01', 90, 135, 540),
('SODA-003', 'WH-CASA-01', 90, 135, 540),
('EAU-001', 'WH-CASA-01', 120, 180, 720),
('EAU-002', 'WH-CASA-01', 150, 225, 900),

-- Riz et autres
('RIZ-001', 'WH-CASA-01', 100, 150, 600),
('THE-001', 'WH-CASA-01', 200, 300, 1000),
('CONF-001', 'WH-CASA-01', 150, 220, 800),
('VIN-001', 'WH-CASA-01', 140, 210, 700),
('SEL-001', 'WH-CASA-01', 180, 270, 900),
('TOMATE-001', 'WH-CASA-01', 280, 420, 1400);

-- Entrepôt Frais Sidi Moumen (WH-CASA-02) - Produits frais et hygiène
INSERT INTO safety_stocks (sku, warehouse_id, safety_stock_qty, reorder_point, max_stock_qty) VALUES
-- Hygiène
('SAV-001', 'WH-CASA-02', 500, 750, 2500),
('SHAM-001', 'WH-CASA-02', 120, 180, 600),
('DENT-001', 'WH-CASA-02', 150, 220, 800),
('LESS-001', 'WH-CASA-02', 50, 75, 300),

-- Chocolat et confiserie
('CHOC-001', 'WH-CASA-02', 200, 300, 1000),
('CHOC-002', 'WH-CASA-02', 350, 525, 1800),
('CAFE-001', 'WH-CASA-02', 120, 180, 600),

-- Produits spéciaux
('MIEL-001', 'WH-CASA-02', 120, 180, 600),
('OLIVE-001', 'WH-CASA-02', 140, 210, 700),
('HARISSA-001', 'WH-CASA-02', 280, 420, 1400),
('SARDINE-001', 'WH-CASA-02', 480, 720, 2400);

-- ============================================
-- VÉRIFICATION
-- ============================================
SELECT 'Fournisseurs insérés: ' || COUNT(*) FROM suppliers;
SELECT 'Entrepôts insérés: ' || COUNT(*) FROM warehouses;
SELECT 'Produits insérés: ' || COUNT(*) FROM products;
SELECT 'Stocks de sécurité configurés: ' || COUNT(*) FROM safety_stocks;