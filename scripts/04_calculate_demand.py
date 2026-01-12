#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
04_calculate_demand.py
======================
Calcul de la demande nette - Version corrigée (chemins relatifs)
"""

import sys
import os
import argparse
import pandas as pd
from datetime import datetime
from pathlib import Path

# Ajustement du path pour utils
sys.path.insert(0, os.path.dirname(__file__))

from utils.logger import setup_logger, log_step
from utils.postgres_client import PostgresClient

logger = setup_logger('calculate')

@log_step("Calcul de la demande nette")
def calculate_demand(execution_date):
    """
    Calcule la demande nette en croisant commandes agrégées et stocks
    """
    
    logger.info(f"🧮 Calcul pour la date: {execution_date}")
    logger.info("")
    
    # ===== CHEMINS CORRIGÉS =====
    # Utiliser le répertoire de travail actuel comme base
    base_dir = Path.cwd()
    
    # Fichier d'entrée : commandes agrégées
    agg_file = base_dir / 'data' / 'processed' / f'aggregated_orders_{execution_date}.csv'
    
    # Fichier d'entrée : stock
    stock_file = base_dir / 'data' / 'raw' / 'stock' / execution_date / 'stock.csv'
    
    # Répertoire de sortie
    output_dir = base_dir / 'data' / 'processed'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # ===== VÉRIFICATION DES FICHIERS =====
    if not agg_file.exists():
        raise FileNotFoundError(f"Fichier introuvable: {agg_file}")
    
    if not stock_file.exists():
        raise FileNotFoundError(f"Fichier introuvable: {stock_file}")
    
    # ===== CHARGEMENT DES DONNÉES =====
    logger.info("📂 Chargement des données...")
    
    # Commandes agrégées
    orders_df = pd.read_csv(agg_file)
    logger.info(f"   ✓ {len(orders_df)} SKUs commandés")
    
    # Stock actuel
    stock_df = pd.read_csv(stock_file)
    logger.info(f"   ✓ {len(stock_df)} lignes de stock")
    logger.info("")
    
    # ===== CONNEXION À POSTGRESQL =====
    logger.info("🔌 Connexion à PostgreSQL pour les données maîtres...")
    
    try:
        pg = PostgresClient(
            host=os.getenv('POSTGRES_HOST', 'postgres'),
            port=int(os.getenv('POSTGRES_PORT', 5432)),
            database=os.getenv('POSTGRES_DB', 'procurement_db'),
            user=os.getenv('POSTGRES_USER', 'procurement_user'),
            password=os.getenv('POSTGRES_PASSWORD', 'procurement_pass')
        )
        
        if pg.test_connection():
            logger.info("   ✓ Connexion établie")
            
            # Charger les produits
            products_df = pg.fetch_dataframe(
                "SELECT sku, product_name, category, supplier_id, unit_price, safety_stock_qty FROM products"
            )
            logger.info(f"   ✓ {len(products_df)} produits chargés")
            logger.info("")
        else:
            logger.warning("   ⚠️ Connexion PostgreSQL échouée, utilisation de données par défaut")
            products_df = pd.DataFrame({
                'sku': orders_df['sku'].unique(),
                'product_name': ['Produit ' + str(i) for i in range(len(orders_df))],
                'category': ['Catégorie A'] * len(orders_df),
                'supplier_id': ['SUP_001'] * len(orders_df),
                'unit_price': [100.0] * len(orders_df),
                'safety_stock_qty': [50] * len(orders_df)
            })
            
    except Exception as e:
        logger.warning(f"   ⚠️ Erreur PostgreSQL: {e}")
        logger.info("   Utilisation de données par défaut")
        products_df = pd.DataFrame({
            'sku': orders_df['sku'].unique(),
            'product_name': ['Produit ' + str(i) for i in range(len(orders_df))],
            'category': ['Catégorie A'] * len(orders_df),
            'supplier_id': ['SUP_001'] * len(orders_df),
            'unit_price': [100.0] * len(orders_df),
            'safety_stock_qty': [50] * len(orders_df)
        })
    
    # ===== AGRÉGATION DU STOCK =====
    logger.info("📊 Agrégation du stock par SKU...")
    
    stock_agg = stock_df.groupby('sku').agg(
        current_stock=('available_qty', 'sum')
    ).reset_index()
    
    logger.info(f"   ✓ {len(stock_agg)} SKUs en stock")
    logger.info("")
    
    # ===== JOINTURES =====
    logger.info("🔗 Jointures des données...")
    
    # Joindre commandes + produits
    demand_df = orders_df.merge(products_df, on='sku', how='left')
    
    # Joindre avec le stock
    demand_df = demand_df.merge(stock_agg, on='sku', how='left')
    
    # Remplir les valeurs manquantes
    demand_df['current_stock'] = demand_df['current_stock'].fillna(0)
    demand_df['safety_stock_qty'] = demand_df['safety_stock_qty'].fillna(50)
    demand_df['unit_price'] = demand_df['unit_price'].fillna(100.0)
    
    logger.info(f"   ✓ {len(demand_df)} SKUs après jointures")
    logger.info("")
    
    # ===== CALCUL DE LA DEMANDE NETTE =====
    logger.info("🧮 Calcul de la demande nette...")
    
    # Demande quotidienne (simplifiée : commandes du jour)
    demand_df['daily_demand'] = demand_df['total_quantity']
    
    # Demande nette = demande - stock + stock de sécurité
    demand_df['net_demand'] = (
        demand_df['daily_demand'] 
        - demand_df['current_stock'] 
        + demand_df['safety_stock_qty']
    )
    
    # Pas de demande négative
    demand_df['net_demand'] = demand_df['net_demand'].clip(lower=0)
    
    # Arrondir à des multiples de 10
    demand_df['rounded_demand'] = (demand_df['net_demand'] / 10).apply(lambda x: int(x + 0.5) * 10)
    
    # Quantité finale à commander (min 0)
    demand_df['final_order_qty'] = demand_df['rounded_demand'].clip(lower=0)
    
    # Valeur de la commande
    demand_df['order_value'] = demand_df['final_order_qty'] * demand_df['unit_price']
    
    logger.info("   ✓ Demandes calculées")
    logger.info("")
    
    # ===== FILTRAGE ET TRI =====
    logger.info("🔍 Filtrage des SKUs à commander...")
    
    # Garder uniquement les SKUs avec une demande > 0
    to_order_df = demand_df[demand_df['final_order_qty'] > 0].copy()
    
    # Trier par valeur décroissante
    to_order_df = to_order_df.sort_values('order_value', ascending=False)
    
    logger.info(f"   ✓ {len(to_order_df)} SKUs à commander")
    logger.info("")
    
    # ===== SAUVEGARDE =====
    logger.info("💾 Sauvegarde des résultats...")
    
    # Colonnes finales
    output_columns = [
        'sku', 'product_name', 'category', 'supplier_id',
        'daily_demand', 'current_stock', 'safety_stock_qty',
        'net_demand', 'rounded_demand', 'final_order_qty',
        'unit_price', 'order_value'
    ]
    
    # Fichier de sortie
    output_file = output_dir / f'net_demand_{execution_date}.csv'
    
    # Sauvegarder
    to_order_df[output_columns].to_csv(output_file, index=False)
    
    logger.info(f"   ✓ Fichier: {output_file}")
    logger.info("")
    
    # ===== STATISTIQUES =====
    total_qty = to_order_df['final_order_qty'].sum()
    total_value = to_order_df['order_value'].sum()
    num_suppliers = to_order_df['supplier_id'].nunique()
    
    logger.info("📊 STATISTIQUES:")
    logger.info(f"   • SKUs à commander: {len(to_order_df)}")
    logger.info(f"   • Quantité totale: {total_qty:,.0f}")
    logger.info(f"   • Valeur totale: {total_value:,.2f} MAD")
    logger.info(f"   • Fournisseurs: {num_suppliers}")
    logger.info("")
    
    logger.info("✅ Calcul terminé avec succès")
    return True

def main():
    parser = argparse.ArgumentParser(
        description='Calcul de la demande nette avec chemins corrigés'
    )
    parser.add_argument(
        '--date',
        type=str,
        default=datetime.now().strftime('%Y-%m-%d'),
        help='Date d\'exécution (YYYY-MM-DD)'
    )
    
    args = parser.parse_args()
    
    try:
        calculate_demand(args.date)
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()