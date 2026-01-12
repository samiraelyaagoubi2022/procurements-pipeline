#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hdfs_client.py
==============
Client pour interagir avec HDFS via WebHDFS (API REST)
"""

import os
import json
import logging
import requests
from pathlib import Path
import pandas as pd

logger = logging.getLogger('pipeline')


class HDFSClient:
    """
    Client pour HDFS utilisant WebHDFS (API REST)
    Plus simple et ne nécessite pas d'installer les outils Hadoop
    """
    
    def __init__(self, namenode=None, port=None):
        """
        Initialise le client HDFS
        
        Args:
            namenode: URL du namenode (défaut: variable d'env HDFS_NAMENODE ou 'namenode')
            port: Port WebHDFS (défaut: 9870)
        """
        self.namenode = namenode or os.getenv('HDFS_NAMENODE', 'namenode')
        self.port = port or int(os.getenv('HDFS_WEBHDFS_PORT', '9870'))
        self.base_url = f"http://{self.namenode}:{self.port}/webhdfs/v1"
        logger.info(f"Client HDFS initialisé: {self.base_url}")
    
    def _make_request(self, method, path, params=None, data=None, files=None):
        """
        Effectue une requête HTTP vers WebHDFS
        
        Args:
            method: GET, PUT, POST, DELETE
            path: Chemin HDFS
            params: Paramètres de requête
            data: Données à envoyer
            files: Fichiers à uploader
            
        Returns:
            Réponse HTTP
        """
        url = f"{self.base_url}{path}"
        params = params or {}
        params['user.name'] = 'root'
        
        try:
            response = requests.request(
                method=method,
                url=url,
                params=params,
                data=data,
                files=files,
                allow_redirects=True,
                timeout=30
            )
            
            if response.status_code not in [200, 201]:
                logger.error(f"Erreur HTTP {response.status_code}: {response.text}")
                response.raise_for_status()
            
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur de requête: {e}")
            raise
    
    def mkdir(self, path, parents=True):
        """
        Crée un répertoire dans HDFS
        
        Args:
            path: Chemin du répertoire
            parents: Créer les parents si nécessaire
        """
        params = {
            'op': 'MKDIRS',
            'permission': '777'
        }
        
        self._make_request('PUT', path, params=params)
        logger.info(f"Répertoire créé: {path}")
    
    def put(self, local_path, hdfs_path, overwrite=False):
        """
        Copie un fichier local vers HDFS
        
        Args:
            local_path: Chemin local du fichier
            hdfs_path: Chemin HDFS de destination
            overwrite: Écraser si existe
        """
        # Étape 1: Créer le fichier (obtenir l'URL de redirection)
        params = {
            'op': 'CREATE',
            'overwrite': 'true' if overwrite else 'false'
        }
        
        response = self._make_request('PUT', hdfs_path, params=params)
        
        # Étape 2: Uploader les données
        with open(local_path, 'rb') as f:
            data = f.read()
            
        upload_url = response.url
        response = requests.put(upload_url, data=data, timeout=60)
        
        if response.status_code in [200, 201]:
            logger.info(f"Fichier copié vers HDFS: {local_path} → {hdfs_path}")
        else:
            raise Exception(f"Échec de l'upload: {response.status_code}")
    
    def upload_file(self, local_path, hdfs_path):
        """
        Alias pour put() - Compatible avec 03_aggregate_orders.py
        Upload un fichier local vers HDFS avec écrasement automatique
        
        Args:
            local_path: Chemin du fichier local
            hdfs_path: Chemin HDFS de destination
        """
        return self.put(local_path, hdfs_path, overwrite=True)
    
    def get(self, hdfs_path, local_path, overwrite=False):
        """
        Copie un fichier HDFS vers le système local
        
        Args:
            hdfs_path: Chemin HDFS source
            local_path: Chemin local de destination
            overwrite: Écraser si existe
        """
        if not overwrite and os.path.exists(local_path):
            raise FileExistsError(f"Le fichier existe déjà: {local_path}")
        
        params = {'op': 'OPEN'}
        response = self._make_request('GET', hdfs_path, params=params)
        
        with open(local_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Fichier récupéré depuis HDFS: {hdfs_path} → {local_path}")
    
    def cat(self, hdfs_path):
        """
        Affiche le contenu d'un fichier HDFS
        
        Args:
            hdfs_path: Chemin du fichier
            
        Returns:
            Contenu du fichier (string)
        """
        params = {'op': 'OPEN'}
        response = self._make_request('GET', hdfs_path, params=params)
        return response.text
    
    def ls(self, hdfs_path):
        """
        Liste les fichiers dans un répertoire HDFS
        
        Args:
            hdfs_path: Chemin du répertoire
            
        Returns:
            Liste des fichiers avec leurs métadonnées
        """
        params = {'op': 'LISTSTATUS'}
        response = self._make_request('GET', hdfs_path, params=params)
        
        data = response.json()
        return data.get('FileStatuses', {}).get('FileStatus', [])
    
    def exists(self, hdfs_path):
        """
        Vérifie si un chemin existe dans HDFS
        
        Args:
            hdfs_path: Chemin à vérifier
            
        Returns:
            True si existe, False sinon
        """
        try:
            params = {'op': 'GETFILESTATUS'}
            self._make_request('GET', hdfs_path, params=params)
            return True
        except:
            return False
    
    def rm(self, hdfs_path, recursive=False):
        """
        Supprime un fichier ou répertoire HDFS
        
        Args:
            hdfs_path: Chemin à supprimer
            recursive: Suppression récursive pour les répertoires
        """
        params = {
            'op': 'DELETE',
            'recursive': 'true' if recursive else 'false'
        }
        
        self._make_request('DELETE', hdfs_path, params=params)
        logger.info(f"Supprimé de HDFS: {hdfs_path}")
    
    def du(self, hdfs_path):
        """
        Affiche l'espace disque utilisé
        
        Args:
            hdfs_path: Chemin à analyser
            
        Returns:
            Taille en bytes
        """
        params = {'op': 'GETCONTENTSUMMARY'}
        response = self._make_request('GET', hdfs_path, params=params)
        
        data = response.json()
        return data.get('ContentSummary', {}).get('length', 0)
    
    def upload_json(self, data, hdfs_path):
        """
        Upload des données JSON vers HDFS
        
        Args:
            data: Données Python (dict ou list)
            hdfs_path: Chemin HDFS de destination
        """
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            temp_path = f.name
        
        try:
            self.put(temp_path, hdfs_path, overwrite=True)
        finally:
            os.unlink(temp_path)
    
    def upload_csv(self, df, hdfs_path):
        """
        Upload un DataFrame vers HDFS au format CSV
        
        Args:
            df: DataFrame pandas
            hdfs_path: Chemin HDFS de destination
        """
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f, index=False, encoding='utf-8')
            temp_path = f.name
        
        try:
            self.put(temp_path, hdfs_path, overwrite=True)
        finally:
            os.unlink(temp_path)
    
    def read_json(self, hdfs_path):
        """
        Lit un fichier JSON depuis HDFS
        
        Args:
            hdfs_path: Chemin du fichier JSON
            
        Returns:
            Données Python
        """
        content = self.cat(hdfs_path)
        return json.loads(content)
    
    def read_csv(self, hdfs_path):
        """
        Lit un fichier CSV depuis HDFS
        
        Args:
            hdfs_path: Chemin du fichier CSV
            
        Returns:
            DataFrame pandas
        """
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_path = f.name
        
        try:
            self.get(hdfs_path, temp_path, overwrite=True)
            df = pd.read_csv(temp_path, encoding='utf-8')
            return df
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_connection(self):
        """
        Test la connexion à HDFS
        
        Returns:
            True si la connexion réussit, False sinon
        """
        try:
            params = {'op': 'LISTSTATUS'}
            self._make_request('GET', '/', params=params)
            logger.info("✅ Connexion HDFS réussie")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur de connexion HDFS: {e}")
            return False


# Exemple d'utilisation
if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Test du client
    client = HDFSClient()
    
    # Test de connexion
    if client.test_connection():
        print("\n✅ Connexion HDFS OK\n")
        
        # Test de création de répertoire
        test_dir = '/test_pipeline'
        if not client.exists(test_dir):
            client.mkdir(test_dir)
            print(f"Répertoire créé: {test_dir}")
        
        # Test d'upload JSON
        test_data = {'test': 'data', 'value': 123}
        test_json_path = f'{test_dir}/test.json'
        client.upload_json(test_data, test_json_path)
        print(f"JSON uploadé: {test_json_path}")
        
        # Test de lecture JSON
        data = client.read_json(test_json_path)
        print(f"JSON lu: {data}")
        
        # Test d'upload CSV
        df = pd.DataFrame({'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']})
        test_csv_path = f'{test_dir}/test.csv'
        client.upload_csv(df, test_csv_path)
        print(f"CSV uploadé: {test_csv_path}")
        
        # Nettoyage
        client.rm(test_dir, recursive=True)
        print(f"Nettoyage effectué")
    else:
        print("\n❌ Connexion HDFS échouée\n")