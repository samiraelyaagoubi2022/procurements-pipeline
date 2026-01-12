#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
postgres_client.py
==================
Client pour interagir avec PostgreSQL
"""

import os
import psycopg2
import pandas as pd
from contextlib import contextmanager
import logging

logger = logging.getLogger('pipeline')


class PostgresClient:
    """Client pour PostgreSQL"""
    
    def __init__(self, host=None, port=None, database=None, user=None, password=None):
        """
        Initialise le client PostgreSQL
        
        Args:
            host: Hôte PostgreSQL (défaut: variable d'env POSTGRES_HOST)
            port: Port (défaut: variable d'env POSTGRES_PORT ou 5432)
            database: Nom de la base (défaut: variable d'env POSTGRES_DB)
            user: Utilisateur (défaut: variable d'env POSTGRES_USER)
            password: Mot de passe (défaut: variable d'env POSTGRES_PASSWORD)
        """
        self.host = host or os.getenv('POSTGRES_HOST', 'localhost')
        self.port = port or int(os.getenv('POSTGRES_PORT', 5432))
        self.database = database or os.getenv('POSTGRES_DB', 'procurement_db')
        self.user = user or os.getenv('POSTGRES_USER', 'procurement_user')
        self.password = password or os.getenv('POSTGRES_PASSWORD', 'procurement_pass')
        
        logger.info(f"Client PostgreSQL initialisé: {self.user}@{self.host}:{self.port}/{self.database}")
    
    @contextmanager
    def get_connection(self):
        """
        Context manager pour obtenir une connexion
        
        Usage:
            with client.get_connection() as conn:
                cur = conn.cursor()
                ...
        """
        conn = None
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Erreur de connexion PostgreSQL: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query, params=None):
        """
        Exécute une requête SQL (INSERT, UPDATE, DELETE)
        
        Args:
            query: Requête SQL
            params: Paramètres de la requête
            
        Returns:
            Nombre de lignes affectées
        """
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            rows_affected = cur.rowcount
            cur.close()
            
            logger.debug(f"Requête exécutée: {rows_affected} lignes affectées")
            return rows_affected
    
    def fetch_dataframe(self, query, params=None):
        """
        Exécute une requête SELECT et retourne un DataFrame
        
        Args:
            query: Requête SQL SELECT
            params: Paramètres de la requête
            
        Returns:
            DataFrame pandas
        """
        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=params)
            logger.debug(f"DataFrame chargé: {len(df)} lignes")
            return df
    
    def fetch_one(self, query, params=None):
        """
        Exécute une requête et retourne une seule ligne
        
        Args:
            query: Requête SQL
            params: Paramètres de la requête
            
        Returns:
            Tuple ou None
        """
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            result = cur.fetchone()
            cur.close()
            return result
    
    def fetch_all(self, query, params=None):
        """
        Exécute une requête et retourne toutes les lignes
        
        Args:
            query: Requête SQL
            params: Paramètres de la requête
            
        Returns:
            Liste de tuples
        """
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            results = cur.fetchall()
            cur.close()
            logger.debug(f"{len(results)} lignes récupérées")
            return results
    
    def get_products(self):
        """Récupère tous les produits actifs"""
        query = """
            SELECT 
                sku, product_name, category, supplier_id,
                unit_price, pack_size, moq, unit_of_measure
            FROM products
            WHERE is_active = TRUE
            ORDER BY sku
        """
        return self.fetch_dataframe(query)
    
    def get_suppliers(self):
        """Récupère tous les fournisseurs actifs"""
        query = """
            SELECT 
                supplier_id, supplier_name, contact_email, contact_phone,
                lead_time_days, min_order_value
            FROM suppliers
            WHERE is_active = TRUE
            ORDER BY supplier_id
        """
        return self.fetch_dataframe(query)
    
    def get_warehouses(self):
        """Récupère tous les entrepôts actifs"""
        query = """
            SELECT 
                warehouse_id, warehouse_name, city, address, capacity_m3
            FROM warehouses
            WHERE is_active = TRUE
            ORDER BY warehouse_id
        """
        return self.fetch_dataframe(query)
    
    def get_safety_stocks(self):
        """Récupère les stocks de sécurité configurés"""
        query = """
            SELECT 
                sku, warehouse_id, safety_stock_qty, 
                reorder_point, max_stock_qty
            FROM safety_stocks
            ORDER BY sku, warehouse_id
        """
        return self.fetch_dataframe(query)
    
    def get_product_details(self, sku):
        """
        Récupère les détails d'un produit
        
        Args:
            sku: Code du produit
            
        Returns:
            DataFrame avec les détails du produit
        """
        query = """
            SELECT 
                p.*,
                s.supplier_name,
                s.lead_time_days,
                s.min_order_value
            FROM products p
            JOIN suppliers s ON p.supplier_id = s.supplier_id
            WHERE p.sku = %s AND p.is_active = TRUE
        """
        return self.fetch_dataframe(query, (sku,))
    
    def test_connection(self):
        """
        Test la connexion à PostgreSQL
        
        Returns:
            True si la connexion réussit, False sinon
        """
        try:
            with self.get_connection() as conn:
                cur = conn.cursor()
                cur.execute('SELECT 1')
                result = cur.fetchone()
                cur.close()
                
                if result == (1,):
                    logger.info("✅ Connexion PostgreSQL réussie")
                    return True
                else:
                    logger.error("❌ Connexion PostgreSQL échouée")
                    return False
        except Exception as e:
            logger.error(f"❌ Erreur de connexion PostgreSQL: {e}")
            return False


# Exemple d'utilisation
if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Test du client
    client = PostgresClient()
    
    # Test de connexion
    if client.test_connection():
        print("\n✅ Connexion OK\n")
        
        # Récupérer les produits
        print("--- PRODUITS ---")
        products = client.get_products()
        print(f"Nombre de produits: {len(products)}")
        print(products.head())
        
        print("\n--- FOURNISSEURS ---")
        suppliers = client.get_suppliers()
        print(f"Nombre de fournisseurs: {len(suppliers)}")
        print(suppliers.head())
        
        print("\n--- ENTREPÔTS ---")
        warehouses = client.get_warehouses()
        print(f"Nombre d'entrepôts: {len(warehouses)}")
        print(warehouses)
    else:
        print("\n❌ Connexion échouée\n")