#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
01_generate_data.py
===================
Génération des données de test (commandes + stocks)
"""

import sys
import os
import argparse
import json
import random
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.utils.logger import setup_logger, log_step
from scripts.utils.postgres_client import PostgresClient

logger = setup_logger('generate')


@log_step('Génération des données')
def generate_data(execution_date, num_orders=500):
    """
    Génère les données de test pour une date donnée
    
    Args:
        execution_date: Date d'exécution (YYYY-MM-DD)
        num_orders: Nombre de commandes à générer
    """
    logger.info(f'📅 Date: {execution_date}')
    logger.info(f'📦 Commandes à générer: {num_orders}')
    logger.info('')
    
    # Connexion PostgreSQL
    pg = PostgresClient()
    
    # Charger les données maîtres
    logger.info('📚 Chargement des données maîtres...')
    products = pg.get_products()
    warehouses = pg.get_warehouses()
    
    logger.info(f'   ✓ {len(products)} produits chargés')
    logger.info(f'   ✓ {len(warehouses)} entrepôts chargés')
    logger.info('')
    
    # Créer les répertoires de sortie
    orders_dir = Path('data/raw/orders') / execution_date
    stock_dir = Path('data/raw/stock') / execution_date
    
    orders_dir.mkdir(parents=True, exist_ok=True)
    stock_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. GÉNÉRER LES COMMANDES
    logger.info('🛒 Génération des commandes...')
    
    stores = ['STORE-CASA-01', 'STORE-CASA-02', 'STORE-CASA-03', 
              'STORE-CASA-04', 'STORE-CASA-05', 'STORE-CASA-06',
              'STORE-CASA-07', 'STORE-CASA-08']
    
    all_orders = []
    
    for i in range(num_orders):
        store_id = random.choice(stores)
        
        # Sélectionner 3-10 produits aléatoires
        num_items = random.randint(3, 10)
        selected_products = products.sample(n=num_items)
        
        items = []
        for _, product in selected_products.iterrows():
            quantity = random.randint(1, 20)
            items.append({
                'sku': product['sku'],
                'quantity': quantity,
                'unit_price': float(product['unit_price'])
            })
        
        order = {
            'order_id': f'ORD-{execution_date}-{i+1:05d}',
            'store_id': store_id,
            'order_date': execution_date,
            'items': items
        }
        
        all_orders.append(order)
    
    # Sauvegarder les commandes
    orders_file = orders_dir / 'orders.json'
    with open(orders_file, 'w', encoding='utf-8') as f:
        json.dump(all_orders, f, ensure_ascii=False, indent=2)
    
    logger.info(f'   ✓ {len(all_orders)} commandes générées')
    logger.info(f'   ✓ Fichier: {orders_file}')
    logger.info('')
    
    # 2. GÉNÉRER LES SNAPSHOTS DE STOCK
    logger.info('📊 Génération des snapshots de stock...')
    
    stock_data = []
    
    for _, warehouse in warehouses.iterrows():
        for _, product in products.iterrows():
            # Stock disponible aléatoire entre 50 et 1000
            available_qty = random.randint(50, 1000)
            # Stock réservé entre 0 et 20% du disponible
            reserved_qty = random.randint(0, int(available_qty * 0.2))
            
            stock_data.append({
                'snapshot_date': execution_date,
                'warehouse_id': warehouse['warehouse_id'],
                'sku': product['sku'],
                'available_qty': available_qty,
                'reserved_qty': reserved_qty
            })
    
    # Sauvegarder le stock
    import pandas as pd
    stock_df = pd.DataFrame(stock_data)
    stock_file = stock_dir / 'stock.csv'
    stock_df.to_csv(stock_file, index=False)
    
    logger.info(f'   ✓ {len(stock_data)} lignes de stock générées')
    logger.info(f'   ✓ Fichier: {stock_file}')
    logger.info('')
    
    # STATISTIQUES
    total_items = sum(len(order['items']) for order in all_orders)
    total_value = sum(
        sum(item['quantity'] * item['unit_price'] for item in order['items'])
        for order in all_orders
    )
    
    logger.info('📊 STATISTIQUES:')
    logger.info(f'   • Commandes: {len(all_orders)}')
    logger.info(f'   • Magasins: {len(stores)}')
    logger.info(f'   • Items commandés: {total_items}')
    logger.info(f'   • Valeur totale: {total_value:,.2f} MAD')
    logger.info(f'   • Lignes de stock: {len(stock_data)}')
    logger.info('')
    
    logger.info('✅ Génération terminée avec succès')
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Génération des données de test'
    )
    parser.add_argument(
        '--date',
        type=str,
        default=datetime.now().strftime('%Y-%m-%d'),
        help='Date d execution (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--num-orders',
        type=int,
        default=500,
        help='Nombre de commandes à générer'
    )
    
    args = parser.parse_args()
    
    try:
        generate_data(args.date, args.num_orders)
        sys.exit(0)
    except Exception as e:
        logger.error(f'❌ Erreur: {e}', exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
