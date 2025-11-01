# -*- coding: utf-8 -*-
"""
ProjectPersistence - Sistema de salvamento e carregamento de projetos .mip
"""

import json
import gzip
import base64
from typing import Dict, Any, Optional
from pathlib import Path


class ProjectPersistence:
    """
    Classe para gerenciar persistência de projetos do Multímetro Inteligente.
    
    Formato .mip:
    - Arquivo JSON comprimido com gzip
    - Contém dados do projeto, pontos e imagem
    - Metadata de versão para compatibilidade
    """
    
    VERSION = "1.0"
    
    @staticmethod
    def save(project_data: Dict[str, Any], file_path: str) -> bool:
        """
        Salva dados do projeto em arquivo .mip
        
        Args:
            project_data: Dicionário com dados do projeto
            file_path: Caminho do arquivo
            
        Returns:
            bool: True se salvou com sucesso
        """
        try:
            # Adiciona metadata
            data_to_save = {
                "version": ProjectPersistence.VERSION,
                "format": "mip",
                "data": project_data
            }
            
            # Converte para JSON
            json_str = json.dumps(data_to_save, indent=2, ensure_ascii=False)
            
            # Comprime com gzip
            compressed_data = gzip.compress(json_str.encode('utf-8'))
            
            # Salva arquivo
            with open(file_path, 'wb') as f:
                f.write(compressed_data)
            
            return True
            
        except Exception as e:
            print(f"Erro ao salvar projeto: {e}")
            return False
    
    @staticmethod
    def load(file_path: str) -> Optional[Dict[str, Any]]:
        """
        Carrega dados do projeto de arquivo .mip
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            Dict com dados do projeto ou None se erro
        """
        try:
            if not Path(file_path).exists():
                return None
            
            # Lê arquivo comprimido
            with open(file_path, 'rb') as f:
                compressed_data = f.read()
            
            # Descomprime
            json_str = gzip.decompress(compressed_data).decode('utf-8')
            
            # Converte de JSON
            loaded_data = json.loads(json_str)
            
            # Verifica versão
            if loaded_data.get("format") != "mip":
                print("Arquivo não é um projeto válido (.mip)")
                return None
            
            version = loaded_data.get("version", "1.0")
            if version != ProjectPersistence.VERSION:
                print(f"Versão do arquivo ({version}) diferente da atual ({ProjectPersistence.VERSION})")
                # Pode implementar migração aqui no futuro
            
            return loaded_data.get("data")
            
        except Exception as e:
            print(f"Erro ao carregar projeto: {e}")
            return None
    
    @staticmethod
    def is_mip_file(file_path: str) -> bool:
        """
        Verifica se arquivo é um projeto .mip válido
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            bool: True se é arquivo .mip válido
        """
        try:
            data = ProjectPersistence.load(file_path)
            return data is not None
        except:
            return False
    
    @staticmethod
    def get_project_info(file_path: str) -> Optional[Dict[str, str]]:
        """
        Obtém informações básicas do projeto sem carregar tudo
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            Dict com informações básicas ou None se erro
        """
        try:
            data = ProjectPersistence.load(file_path)
            if not data:
                return None
            
            project_info = data.get("project", {})
            points = data.get("points", [])
            
            return {
                "name": project_info.get("name", "Projeto sem nome"),
                "board_model": project_info.get("board_model", "Modelo desconhecido"),
                "point_count": str(len(points)),
                "has_image": "image_data" in data,
                "file_size": str(Path(file_path).stat().st_size)
            }
            
        except Exception:
            return None
    
    @staticmethod
    def export_to_json(file_path: str, output_path: str) -> bool:
        """
        Exporta projeto .mip para JSON não comprimido (debug/backup)
        
        Args:
            file_path: Caminho do arquivo .mip
            output_path: Caminho do arquivo JSON de saída
            
        Returns:
            bool: True se exportou com sucesso
        """
        try:
            data = ProjectPersistence.load(file_path)
            if not data:
                return False
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Erro ao exportar para JSON: {e}")
            return False