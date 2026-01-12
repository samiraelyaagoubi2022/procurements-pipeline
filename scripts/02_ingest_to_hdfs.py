#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
02_ingest_to_hdfs.py
====================
Ingestion COMPLÈTE des données dans HDFS (JSON brut + agrégés)
Version améliorée avec upload du fichier brut
"""

import sys
import os
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd
import requests

# Ajustement du path pour utils
sys.path.insert(0, os.path.dirname(__file__))

from utils.logger import setup_logger, log_step
from utils.presto_client import PrestoClient

logger = setup_logger('hdfs_loader')

# Configuration
NAMENODE_URL = os.getenv('NAMENODE_URL', 'http://namenode:9870')
HDFS_BASE_PATH = '/raw/orders'
TRINO_HOST = os.getenv('TRINO_HOST', 'trino')
TRINO_PORT = int(os.getenv('TRINO_PORT', '8080'))


def upload_to_hdfs(local_file_path, hdfs_path):
    """
    Upload un fichier vers HDFS via WebHDFS API
    
    Args:
        local_file_path: Chemin du fichier local
        hdfs_path: Chemin de destination dans HDFS
        
    Returns:
        True si succès, False sinon
    """
    
    # Créer le répertoire parent si nécessaire
    parent_dir = '/'.join(hdfs_path.split('/')[:-1])
    mkdir_url = f"{NAMENODE_URL}/webhdfs/v1{parent_dir}?op=MKDIRS&user.name=root"
    
    try:
        response = requests.put(mkdir_url, timeout=10)
        if response.status_code not in [200, 201]:
            logger.warning(f"   ⚠️ Création répertoire {parent_dir}: {response.status_code}")
    except Exception as e:
        logger.warning(f"   ⚠️ Erreur création répertoire: {e}")
    
    # Upload du fichier
    create_url = f"{NAMENODE_URL}/webhdfs/v1{hdfs_path}?op=CREATE&overwrite=true&user.name=root"
    
    try:
        # Étape 1: Obtenir l'URL de redirection
        response = requests.put(create_url, allow_redirects=False, timeout=10)
        
        if response.status_code == 307:
            redirect_url = response.headers['Location']
            
            # Étape 2: Uploader les données
            with open(local_file_path, 'rb') as f:
                upload_response = requests.put(
                    redirect_url,
                    data=f,
                    headers={'Content-Type': 'application/octet-stream'},
                    timeout=120  # Timeout plus long pour gros fichiers
                )
                
                if upload_response.status_code in [200, 201]:
                    file_size = os.path.getsize(local_file_path)
                    size_mb = file_size / (1024 * 1024)
                    logger.info(f"   ✅ Uploadé: {hdfs_path} ({size_mb:.1f} MB)")
                    return True
                else:
                    logger.error(f"   ❌ Erreur upload: {upload_response.status_code}")
                    return False
        else:
            logger.error(f"   ❌ Pas de redirection 307: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"   ❌ Erreur lors de l'upload: {e}")
        return False


def prepare_data_files(execution_date):
    """
    Prépare les fichiers Parquet et JSON Lines à partir du CSV
    
    Args:
        execution_date: Date au format YYYY-MM-DD
        
    Returns:
        Dict avec les chemins des fichiers créés
    """
    
    logger.info("📁 Préparation des fichiers de données agrégées...")
    
    # Chemins
    base_dir = Path.cwd()
    processed_dir = base_dir / 'data' / 'processed'
    
    csv_file = processed_dir / f'aggregated_orders_{execution_date}.csv'
    parquet_file = processed_dir / f'aggregated_orders_{execution_date}.parquet'
    jsonl_file = processed_dir / f'aggregated_orders_{execution_date}.jsonl'
    
    files = {
        'csv': csv_file,
        'parquet': None,
        'jsonl': None
    }
    
    # Vérifier que le CSV existe
    if not csv_file.exists():
        logger.error(f"   ❌ Fichier CSV introuvable: {csv_file}")
        return files
    
    try:
        # Charger les données
        df = pd.read_csv(csv_file)
        logger.info(f"   ✓ {len(df):,} lignes chargées depuis CSV")
        
        # 1. Créer le fichier Parquet (format optimisé pour Trino)
        df.to_parquet(parquet_file, index=False, engine='pyarrow')
        parquet_size = os.path.getsize(parquet_file)
        logger.info(f"   ✓ Parquet créé: {parquet_size:,} bytes")
        files['parquet'] = parquet_file
        
        # 2. Créer le fichier JSON Lines (format texte pour débogage)
        df.to_json(jsonl_file, orient='records', lines=True)
        jsonl_size = os.path.getsize(jsonl_file)
        logger.info(f"   ✓ JSON Lines créé: {jsonl_size:,} bytes")
        files['jsonl'] = jsonl_file
        
        # Comparaison des tailles
        ratio = jsonl_size / parquet_size
        logger.info(f"   📏 Ratio JSON/Parquet: {ratio:.1f}x (JSON est {ratio:.1f}x plus gros)")
        
        return files
        
    except Exception as e:
        logger.error(f"   ❌ Erreur préparation fichiers: {e}")
        return files


def upload_raw_orders(execution_date):
    """
    Upload le fichier JSON brut des commandes dans HDFS
    
    Args:
        execution_date: Date au format YYYY-MM-DD
        
    Returns:
        True si succès, False sinon
    """
    
    logger.info("📦 Upload du fichier brut des commandes...")
    
    # Chemin du fichier JSON brut
    base_dir = Path.cwd()
    raw_orders_file = base_dir / 'data' / 'raw' / 'orders' / execution_date / 'orders.json'
    
    if not raw_orders_file.exists():
        logger.warning(f"   ⚠️ Fichier brut non trouvé: {raw_orders_file}")
        logger.warning("   → Ceci est normal si vous n'avez pas généré de données pour cette date")
        return False
    
    # Taille du fichier
    file_size = os.path.getsize(raw_orders_file)
    size_mb = file_size / (1024 * 1024)
    logger.info(f"   📏 Taille du fichier: {size_mb:.1f} MB")
    
    # Upload dans HDFS
    hdfs_path = f"{HDFS_BASE_PATH}/{execution_date}/orders.json"
    logger.info(f"   → Destination HDFS: {hdfs_path}")
    
    if upload_to_hdfs(str(raw_orders_file), hdfs_path):
        logger.info(f"   ✅ Fichier brut uploadé avec succès")
        
        # Calcul du nombre de blocs attendus
        block_size_mb = 128
        expected_blocks = int(size_mb / block_size_mb) + (1 if size_mb % block_size_mb > 0 else 0)
        
        if expected_blocks > 1:
            logger.info(f"   📊 Taille > 128 MB → ~{expected_blocks} blocs HDFS attendus")
        else:
            logger.info(f"   📊 Taille < 128 MB → 1 bloc HDFS")
        
        return True
    else:
        logger.error(f"   ❌ Échec upload du fichier brut")
        return False


@log_step("Ingestion des données dans HDFS")
def ingest_to_hdfs(execution_date):
    """
    Ingère les données dans HDFS avec séparation JSON/Parquet
    
    Args:
        execution_date: Date au format YYYY-MM-DD
        
    Returns:
        True si succès, False sinon
    """
    
    logger.info(f"📦 Ingestion HDFS pour la date: {execution_date}")
    logger.info("")
    
    # ===== 1. UPLOAD DU FICHIER BRUT (NOUVEAU) =====
    raw_uploaded = upload_raw_orders(execution_date)
    logger.info("")
    
    # ===== 2. PRÉPARATION DES FICHIERS AGRÉGÉS =====
    files = prepare_data_files(execution_date)
    
    if not files['parquet'] or not files['jsonl']:
        logger.error("❌ Impossible de préparer les fichiers agrégés")
        return False
    
    logger.info("")
    
    # ===== 3. UPLOAD DES FICHIERS AGRÉGÉS VERS HDFS =====
    logger.info("📤 Upload des fichiers agrégés vers HDFS...")
    
    upload_success = True
    
    # Upload Parquet (dans sous-répertoire /parquet)
    hdfs_parquet_path = f"{HDFS_BASE_PATH}/{execution_date}/parquet/orders.parquet"
    logger.info(f"   → Parquet: {hdfs_parquet_path}")
    
    if not upload_to_hdfs(str(files['parquet']), hdfs_parquet_path):
        logger.error("   ❌ Échec upload Parquet")
        upload_success = False
    
    # Upload JSON Lines (dans sous-répertoire /json)
    hdfs_json_path = f"{HDFS_BASE_PATH}/{execution_date}/json/orders.jsonl"
    logger.info(f"   → JSON: {hdfs_json_path}")
    
    if not upload_to_hdfs(str(files['jsonl']), hdfs_json_path):
        logger.warning("   ⚠️ Échec upload JSON (non bloquant)")
    
    if not upload_success:
        logger.error("❌ Échec des uploads critiques")
        return False
    
    logger.info("")
    
    # ===== 4. CRÉATION DES TABLES TRINO =====
    logger.info("🔧 Création des tables Trino...")
    
    try:
        # Connexion à Trino
        presto = PrestoClient(host=TRINO_HOST, port=TRINO_PORT)
        
        if not presto.test_connection():
            logger.warning("⚠️ Connexion Trino échouée, tables non créées")
            return True  # Upload OK, mais pas de tables
        
        # Créer les tables hybrides
        results = presto.create_hybrid_tables(execution_date, HDFS_BASE_PATH)
        
        if results['parquet']:
            logger.info("   ✅ Table Parquet opérationnelle")
        else:
            logger.error("   ❌ Échec création table Parquet")
            return False
        
        if results['json']:
            logger.info("   ✅ Table JSON disponible")
        else:
            logger.warning("   ⚠️ Table JSON non créée")
        
        # Vérifier les statistiques
        logger.info("")
        logger.info("📊 Statistiques des tables:")
        
        table_suffix = execution_date.replace('-', '_')
        
        # Stats Parquet
        parquet_stats = presto.get_table_stats(f'orders_{table_suffix}')
        if parquet_stats['exists']:
            logger.info(f"   • Parquet: {parquet_stats['row_count']:,} lignes")
        
        # Stats JSON
        if results['json']:
            json_stats = presto.get_table_stats(f'orders_{table_suffix}_json')
            if json_stats['exists']:
                logger.info(f"   • JSON: {json_stats['row_count']:,} lignes")
        
        presto.close()
        
    except Exception as e:
        logger.warning(f"⚠️ Erreur Trino: {e}")
        logger.info("   Données uploadées dans HDFS, mais tables non créées")
        return True  # Upload OK même si tables non créées
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("✅ INGESTION HDFS TERMINÉE AVEC SUCCÈS")
    logger.info("=" * 80)
    logger.info(f"📍 Localisation:")
    if raw_uploaded:
        logger.info(f"   • Fichier brut: {HDFS_BASE_PATH}/{execution_date}/orders.json")
    logger.info(f"   • Parquet (analyse): {HDFS_BASE_PATH}/{execution_date}/parquet/")
    logger.info(f"   • JSON (débogage): {HDFS_BASE_PATH}/{execution_date}/json/")
    logger.info("")
    logger.info(f"🔍 Utilisation:")
    logger.info(f"   • Requêtes rapides: SELECT * FROM hive.default.orders_{execution_date.replace('-', '_')}")
    if results.get('json'):
        logger.info(f"   • Débogage: SELECT * FROM hive.default.orders_{execution_date.replace('-', '_')}_json")
    logger.info("")
    if raw_uploaded:
        logger.info(f"🔎 Vérifier le partitionnement:")
        logger.info(f"   hdfs fsck /raw/orders/{execution_date}/orders.json -files -blocks -locations")
    logger.info("=" * 80)
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Ingestion COMPLÈTE des données dans HDFS (brut + agrégés)'
    )
    parser.add_argument(
        '--date',
        type=str,
        default=datetime.now().strftime('%Y-%m-%d'),
        help='Date d\'exécution (YYYY-MM-DD)'
    )
    
    args = parser.parse_args()
    
    try:
        success = ingest_to_hdfs(args.date)
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()