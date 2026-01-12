#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
03_aggregate_orders.py
======================
Agrégation des commandes - Version STRICTE avec Trino obligatoire
Conforme aux exigences du projet (Section IV.1.3)
"""

import sys
import os
import json
import argparse
import pandas as pd
from datetime import datetime
from pathlib import Path

# Ajustement du path pour utils
sys.path.insert(0, os.path.dirname(__file__))

from utils.logger import setup_logger, log_step
from utils.presto_client import PrestoClient
from utils.hdfs_client import HDFSClient

logger = setup_logger('aggregate')


def prepare_parquet_for_trino(execution_date):
    """
    Convertit JSON en Parquet et le copie dans HDFS
    Retourne True si succès
    """
    try:
        logger.info("📁 Préparation des données pour Trino...")
        
        # Lire le JSON localement
        json_file = Path(f'data/raw/orders/{execution_date}/orders.json')
        
        if not json_file.exists():
            logger.error(f"   ❌ Fichier JSON non trouvé: {json_file}")
            return False
        
        with open(json_file, 'r') as f:
            orders = json.load(f)
        
        # Aplatir les données (dénormalisation)
        records = []
        for order in orders:
            for item in order['items']:
                records.append({
                    'order_id': order['order_id'],
                    'store_id': order['store_id'],
                    'order_date': order['order_date'],
                    'sku': item.get('sku', item.get('product_id', '')),
                    'quantity': item['quantity'],
                    'unit_price': item['unit_price']
                })
        
        df = pd.DataFrame(records)
        
        # Sauvegarder en Parquet LOCAL
        parquet_dir = Path(f'data/raw/orders/{execution_date}')
        parquet_dir.mkdir(parents=True, exist_ok=True)
        parquet_file = parquet_dir / 'orders.parquet'
        
        df.to_parquet(parquet_file, index=False, engine='pyarrow')
        logger.info(f"   ✓ Fichier Parquet créé: {parquet_file} ({len(df)} lignes)")
        
        # Copier le Parquet dans HDFS dans un sous-répertoire dédié
        hdfs = HDFSClient()
        parquet_hdfs_path = f'/raw/orders/{execution_date}/parquet/orders.parquet'
        
        hdfs.upload_file(str(parquet_file), parquet_hdfs_path)
        logger.info(f"   ✓ Parquet copié dans HDFS: {parquet_hdfs_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"   ❌ Erreur lors de la préparation Parquet: {e}")
        return False


def aggregate_with_trino(presto, table_name, execution_date):
    """
    Agrège les données avec Trino (OBLIGATOIRE selon le projet)
    """
    
    logger.info(f"   📊 Création de la table externe {table_name}...")
    
    # ✅ CORRECTION: Pointer vers le sous-répertoire Parquet UNIQUEMENT
    query_create = f"""
    CREATE TABLE IF NOT EXISTS hive.default.{table_name} (
        order_id VARCHAR,
        store_id VARCHAR,
        order_date VARCHAR,
        sku VARCHAR,
        quantity INTEGER,
        unit_price DOUBLE
    )
    WITH (
        external_location = 'hdfs://namenode:9000/raw/orders/{execution_date}/parquet/',
        format = 'PARQUET'
    )
    """
    
    presto.execute_query(query_create)
    logger.info(f"   ✓ Table hive.default.{table_name} créée")
    
    # Vérifier que la table contient des données
    count_result = presto.fetch_all(f"SELECT COUNT(*) FROM hive.default.{table_name}")
    count = count_result[0][0]
    logger.info(f"   ✓ Vérification: {count:,} lignes dans la table")
    
    if count == 0:
        raise Exception(f"Table {table_name} vide dans Trino - vérifiez le format Parquet dans HDFS")
    
    # Requête d'agrégation (conformément au projet)
    logger.info("   🔢 Exécution de l'agrégation SQL via Trino...")
    
    query_agg = f"""
    SELECT 
        sku,
        SUM(quantity) as total_quantity,
        COUNT(DISTINCT order_id) as num_orders,
        COUNT(DISTINCT store_id) as num_stores,
        AVG(CAST(quantity AS DOUBLE)) as avg_quantity_per_order,
        SUM(quantity * unit_price) as total_value
    FROM 
        hive.default.{table_name}
    WHERE 
        order_date = '{execution_date}'
    GROUP BY 
        sku
    ORDER BY 
        total_quantity DESC
    """
    
    agg_df = presto.fetch_dataframe(query_agg)
    logger.info(f"   ✅ {len(agg_df)} SKUs agrégés via Trino")
    
    return agg_df


@log_step("Agrégation des commandes")
def aggregate_orders(execution_date):
    """
    Agrège les commandes par SKU
    VERSION STRICTE: Trino est OBLIGATOIRE (pas de fallback)
    """
    
    logger.info(f"📊 Agrégation pour la date: {execution_date}")
    logger.info("")
    
    # ===== CONNEXION TRINO (OBLIGATOIRE) =====
    logger.info("🔌 Connexion à Presto/Trino (REQUIS)...")
    
    try:
        presto = PrestoClient(
            host=os.getenv('TRINO_HOST', 'trino'),
            port=int(os.getenv('TRINO_PORT', 8080))
        )
        
        if not presto.test_connection():
            logger.error("❌ Connexion Presto échouée")
            logger.error("❌ Le projet EXIGE l'utilisation de Trino pour les agrégations")
            logger.error("   Vérifiez que le service Trino est démarré")
            return False
        
        logger.info("   ✓ Connexion Presto établie")
        logger.info("")
        
    except Exception as e:
        logger.error(f"❌ Erreur de connexion Trino: {e}")
        logger.error("❌ Le projet EXIGE l'utilisation de Trino - Impossible de continuer")
        return False
    
    # ===== PRÉPARATION PARQUET =====
    logger.info("📦 Conversion JSON → Parquet...")
    
    if not prepare_parquet_for_trino(execution_date):
        logger.error("❌ Impossible de préparer les données pour Trino")
        return False
    
    logger.info("")
    
    # ===== AGRÉGATION VIA TRINO (OBLIGATOIRE) =====
    logger.info("🔢 Agrégation via Trino...")
    
    table_name = f'orders_{execution_date.replace("-", "_")}'
    
    try:
        agg_df = aggregate_with_trino(presto, table_name, execution_date)
        logger.info("   ✅ Agrégation Trino réussie")
        
    except Exception as e:
        logger.error(f"❌ Échec agrégation Trino: {e}")
        logger.error("❌ Le projet EXIGE l'utilisation de Trino - Arrêt du pipeline")
        presto.close()
        return False
    
    presto.close()
    
    # ===== SAUVEGARDE DES RÉSULTATS =====
    logger.info("")
    logger.info("💾 Sauvegarde des résultats...")
    output_dir = Path('data/processed')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f'aggregated_orders_{execution_date}.csv'
    agg_df.to_csv(output_file, index=False)
    
    logger.info(f"   ✓ Fichier: {output_file}")
    logger.info("")
    
    # ===== STATISTIQUES =====
    total_qty = agg_df['total_quantity'].sum()
    total_value = agg_df['total_value'].sum()
    
    logger.info("📊 STATISTIQUES:")
    logger.info(f"   • SKUs: {len(agg_df)}")
    logger.info(f"   • Quantité totale: {total_qty:,.0f}")
    logger.info(f"   • Valeur totale: {total_value:,.2f} MAD")
    logger.info("")
    
    logger.info("=" * 80)
    logger.info("✅ AGRÉGATION TERMINÉE VIA TRINO")
    logger.info("=" * 80)
    logger.info("")
    logger.info("📌 Conformité au projet:")
    logger.info("   ✅ Compute Engine: Trino/Presto")
    logger.info("   ✅ Read data from HDFS: Parquet depuis /raw/orders/")
    logger.info("   ✅ Execute SQL transformations: Agrégation GROUP BY")
    logger.info("=" * 80)
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Agrégation des commandes - VERSION STRICTE TRINO'
    )
    parser.add_argument(
        '--date',
        type=str,
        default=datetime.now().strftime('%Y-%m-%d'),
        help='Date d\'exécution (YYYY-MM-DD)'
    )
    
    args = parser.parse_args()
    
    try:
        success = aggregate_orders(args.date)
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()