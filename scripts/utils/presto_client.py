#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
presto_client.py
================
Client Trino amélioré avec support hybride JSON/Parquet
"""

import os
import logging
import pandas as pd
import trino
from typing import Optional, List, Dict, Any

logger = logging.getLogger('pipeline')


class PrestoClient:
    """Client Trino avec support multi-format (JSON, Parquet)"""

    def __init__(self, host=None, port=None, catalog='hive', schema='default', user=None):
        """
        Initialise le client Trino
        
        Args:
            host: Hôte Trino (défaut: env TRINO_HOST ou 'trino')
            port: Port Trino (défaut: env TRINO_PORT ou 8080)
            catalog: Catalog Hive (défaut: 'hive')
            schema: Schema (défaut: 'default')
            user: Utilisateur (défaut: env TRINO_USER ou 'procurement_user')
        """
        # ⚡ Priorité: argument > TRINO_HOST > PRESTO_HOST > 'trino'
        self.host = host or os.getenv('TRINO_HOST') or os.getenv('PRESTO_HOST') or 'trino'
        self.port = port or int(os.getenv('TRINO_PORT') or os.getenv('PRESTO_PORT') or 8080)
        self.catalog = catalog
        self.schema = schema
        self.user = user or os.getenv('TRINO_USER') or os.getenv('PRESTO_USER') or 'procurement_user'

        logger.info(
            f"🔌 Client Trino initialisé: {self.host}:{self.port} "
            f"({self.catalog}.{self.schema}) user={self.user}"
        )

        try:
            self.conn = trino.dbapi.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                catalog=self.catalog,
                schema=self.schema
            )
            logger.info("✅ Connexion Trino établie")
        except Exception as e:
            logger.error(f"❌ Erreur connexion Trino: {e}")
            raise

    def get_cursor(self):
        """Retourne un nouveau curseur"""
        return self.conn.cursor()

    def execute(self, query: str) -> None:
        """
        Exécute une requête sans retour de résultat
        Alias pour execute_query (rétrocompatibilité)
        """
        self.execute_query(query)

    def execute_query(self, query: str) -> None:
        """Exécute une requête DDL ou DML"""
        try:
            cur = self.get_cursor()
            cur.execute(query)
            cur.close()
            logger.debug(f"✓ Requête exécutée: {query[:100]}...")
        except Exception as e:
            logger.error(f"❌ Erreur exécution requête: {e}")
            logger.error(f"   Requête: {query}")
            raise

    def fetch_all(self, query: str) -> List[tuple]:
        """
        Exécute une requête et retourne toutes les lignes
        
        Returns:
            List de tuples représentant les lignes
        """
        try:
            cur = self.get_cursor()
            cur.execute(query)
            rows = cur.fetchall()
            cur.close()
            logger.debug(f"✓ {len(rows)} lignes récupérées")
            return rows
        except Exception as e:
            logger.error(f"❌ Erreur fetch_all: {e}")
            logger.error(f"   Requête: {query}")
            raise

    def fetch_dataframe(self, query: str) -> pd.DataFrame:
        """
        Exécute une requête et retourne un DataFrame pandas
        
        Returns:
            DataFrame pandas avec les résultats
        """
        try:
            cur = self.get_cursor()
            cur.execute(query)
            
            # Récupérer les noms de colonnes
            columns = [desc[0] for desc in cur.description]
            
            # Récupérer les données
            rows = cur.fetchall()
            cur.close()
            
            # Créer le DataFrame
            df = pd.DataFrame(rows, columns=columns)
            logger.info(f"✓ DataFrame chargé: {len(df)} lignes × {len(columns)} colonnes")
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Erreur fetch_dataframe: {e}")
            logger.error(f"   Requête: {query}")
            raise

    def test_connection(self) -> bool:
        """
        Teste la connexion à Trino
        
        Returns:
            True si connexion OK, False sinon
        """
        try:
            result = self.fetch_all("SELECT 1 as test")
            
            # Trino retourne [[1]], pas [(1,)]
            if result and len(result) > 0 and result[0][0] == 1:
                logger.info("✅ Test connexion Trino réussi")
                return True
            
            logger.warning(f"⚠️ Test connexion: résultat inattendu: {result}")
            return False
            
        except Exception as e:
            logger.error(f"❌ Test connexion Trino échoué: {e}")
            return False

    def drop_table(self, table_name: str, catalog: Optional[str] = None, 
                   schema: Optional[str] = None) -> None:
        """
        Supprime une table si elle existe
        
        Args:
            table_name: Nom de la table
            catalog: Catalog (défaut: self.catalog)
            schema: Schema (défaut: self.schema)
        """
        catalog = catalog or self.catalog
        schema = schema or self.schema
        
        query = f"DROP TABLE IF EXISTS {catalog}.{schema}.{table_name}"
        
        try:
            self.execute_query(query)
            logger.info(f"🗑️  Table supprimée: {catalog}.{schema}.{table_name}")
        except Exception as e:
            logger.warning(f"⚠️ Erreur suppression table {table_name}: {e}")

    def create_parquet_table(self, table_name: str, hdfs_path: str,
                            catalog: Optional[str] = None,
                            schema: Optional[str] = None) -> bool:
        """
        Crée une table externe Parquet pointant vers HDFS
        
        Args:
            table_name: Nom de la table (ex: 'orders_2026_01_22')
            hdfs_path: Chemin HDFS (ex: '/raw/orders/2026-01-22/parquet')
            catalog: Catalog (défaut: self.catalog)
            schema: Schema (défaut: self.schema)
            
        Returns:
            True si succès, False sinon
        """
        catalog = catalog or self.catalog
        schema = schema or self.schema
        
        # Assurer que le chemin HDFS est complet
        if not hdfs_path.startswith('hdfs://'):
            hdfs_path = f"hdfs://namenode:9000{hdfs_path}"
        
        # Schéma pour les données AGRÉGÉES (aggregated_orders)
        query = f"""
        CREATE TABLE IF NOT EXISTS {catalog}.{schema}.{table_name} (
            sku VARCHAR,
            total_quantity BIGINT,
            num_orders BIGINT,
            num_stores BIGINT,
            avg_quantity_per_order DOUBLE,
            total_value DOUBLE
        )
        WITH (
            external_location = '{hdfs_path}',
            format = 'PARQUET'
        )
        """
        
        try:
            # Supprimer l'ancienne table
            self.drop_table(table_name, catalog, schema)
            
            # Créer la nouvelle table
            self.execute_query(query)
            logger.info(f"✅ Table Parquet créée: {catalog}.{schema}.{table_name}")
            
            # Vérifier que la table contient des données
            count_result = self.fetch_all(
                f"SELECT COUNT(*) FROM {catalog}.{schema}.{table_name}"
            )
            row_count = count_result[0][0] if count_result else 0
            logger.info(f"   📊 {row_count:,} lignes dans la table")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur création table Parquet {table_name}: {e}")
            return False

    def create_json_table(self, table_name: str, hdfs_path: str,
                         catalog: Optional[str] = None,
                         schema: Optional[str] = None) -> bool:
        """
        Crée une table externe JSON Lines pointant vers HDFS
        
        Args:
            table_name: Nom de la table (ex: 'orders_2026_01_22_json')
            hdfs_path: Chemin HDFS (ex: '/raw/orders/2026-01-22/json')
            catalog: Catalog (défaut: self.catalog)
            schema: Schema (défaut: self.schema)
            
        Returns:
            True si succès, False sinon
        """
        catalog = catalog or self.catalog
        schema = schema or self.schema
        
        # Assurer que le chemin HDFS est complet
        if not hdfs_path.startswith('hdfs://'):
            hdfs_path = f"hdfs://namenode:9000{hdfs_path}"
        
        # Schéma pour les données AGRÉGÉES (aggregated_orders)
        query = f"""
        CREATE TABLE IF NOT EXISTS {catalog}.{schema}.{table_name} (
            sku VARCHAR,
            total_quantity BIGINT,
            num_orders BIGINT,
            num_stores BIGINT,
            avg_quantity_per_order DOUBLE,
            total_value DOUBLE
        )
        WITH (
            external_location = '{hdfs_path}',
            format = 'JSON'
        )
        """
        
        try:
            # Supprimer l'ancienne table
            self.drop_table(table_name, catalog, schema)
            
            # Créer la nouvelle table
            self.execute_query(query)
            logger.info(f"✅ Table JSON créée: {catalog}.{schema}.{table_name}")
            
            # Vérifier que la table contient des données
            try:
                count_result = self.fetch_all(
                    f"SELECT COUNT(*) FROM {catalog}.{schema}.{table_name}"
                )
                row_count = count_result[0][0] if count_result else 0
                logger.info(f"   📊 {row_count:,} lignes dans la table")
            except Exception as e:
                logger.warning(f"   ⚠️ Impossible de compter les lignes JSON: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur création table JSON {table_name}: {e}")
            return False

    def create_hybrid_tables(self, date_str: str, 
                            base_hdfs_path: str = '/raw/orders') -> Dict[str, bool]:
        """
        Crée les tables Parquet ET JSON pour une date donnée
        
        Args:
            date_str: Date au format YYYY-MM-DD
            base_hdfs_path: Chemin de base HDFS
            
        Returns:
            Dict avec status de création: {'parquet': bool, 'json': bool}
        """
        table_suffix = date_str.replace('-', '_')
        
        results = {
            'parquet': False,
            'json': False
        }
        
        # 1. Créer la table Parquet (prioritaire pour analyse)
        parquet_table = f"orders_{table_suffix}"
        parquet_path = f"{base_hdfs_path}/{date_str}/parquet"
        
        results['parquet'] = self.create_parquet_table(
            parquet_table, 
            parquet_path
        )
        
        # 2. Créer la table JSON (pour débogage)
        json_table = f"orders_{table_suffix}_json"
        json_path = f"{base_hdfs_path}/{date_str}/json"
        
        results['json'] = self.create_json_table(
            json_table,
            json_path
        )
        
        # Résumé
        if results['parquet'] and results['json']:
            logger.info(f"✅ Tables hybrides créées pour {date_str}")
        elif results['parquet']:
            logger.info(f"✅ Table Parquet créée (JSON non disponible) pour {date_str}")
        else:
            logger.warning(f"⚠️ Échec création tables pour {date_str}")
        
        return results

    def list_tables(self, catalog: Optional[str] = None,
                   schema: Optional[str] = None) -> List[str]:
        """
        Liste toutes les tables d'un schema
        
        Returns:
            Liste des noms de tables
        """
        catalog = catalog or self.catalog
        schema = schema or self.schema
        
        try:
            query = f"SHOW TABLES FROM {catalog}.{schema}"
            results = self.fetch_all(query)
            tables = [row[0] for row in results]
            logger.info(f"📋 {len(tables)} tables trouvées dans {catalog}.{schema}")
            return tables
        except Exception as e:
            logger.error(f"❌ Erreur liste tables: {e}")
            return []

    def get_table_stats(self, table_name: str,
                       catalog: Optional[str] = None,
                       schema: Optional[str] = None) -> Dict[str, Any]:
        """
        Récupère les statistiques d'une table
        
        Returns:
            Dict avec statistiques: {'row_count', 'size_bytes', etc.}
        """
        catalog = catalog or self.catalog
        schema = schema or self.schema
        
        stats = {
            'table_name': table_name,
            'row_count': 0,
            'exists': False
        }
        
        try:
            # Compter les lignes
            count_query = f"SELECT COUNT(*) FROM {catalog}.{schema}.{table_name}"
            result = self.fetch_all(count_query)
            stats['row_count'] = result[0][0] if result else 0
            stats['exists'] = True
            
            logger.info(f"📊 {table_name}: {stats['row_count']:,} lignes")
            
        except Exception as e:
            logger.warning(f"⚠️ Table {table_name} non accessible: {e}")
        
        return stats

    def close(self):
        """Ferme la connexion Trino"""
        try:
            if self.conn:
                self.conn.close()
                logger.info("🔌 Connexion Trino fermée")
        except Exception as e:
            logger.warning(f"⚠️ Erreur fermeture connexion: {e}")

    def __enter__(self):
        """Support du context manager"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Fermeture automatique avec context manager"""
        self.close()