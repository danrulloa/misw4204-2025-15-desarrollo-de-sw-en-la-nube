"""
Tests para init_db.py sin base de datos
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Agregar el directorio padre al path para importar app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.init_db import init_db


class TestInitDB:
    """Tests para funciones de inicialización de base de datos"""

    @patch('app.init_db.Base.metadata.create_all')
    @patch('app.init_db.engine')
    def test_init_db_success(self, mock_engine, mock_create_all):
        """Test que init_db ejecuta correctamente"""
        # Configurar mocks
        mock_engine.url = "postgresql://test:test@localhost/test"
        
        # Ejecutar función
        init_db()
        
        # Verificar que se llamó create_all
        mock_create_all.assert_called_once_with(bind=mock_engine)

    @patch('app.init_db.Base.metadata.create_all')
    @patch('app.init_db.engine')
    def test_init_db_with_different_url(self, mock_engine, mock_create_all):
        """Test que init_db maneja diferentes URLs de base de datos"""
        # Configurar mock con URL diferente
        mock_engine.url = "sqlite:///test.db"
        
        # Ejecutar función
        init_db()
        
        # Verificar que se llamó create_all
        mock_create_all.assert_called_once_with(bind=mock_engine)

    @patch('app.init_db.Base.metadata.create_all')
    @patch('app.init_db.engine')
    def test_init_db_handles_exception(self, mock_engine, mock_create_all):
        """Test que init_db maneja excepciones de create_all"""
        # Configurar mock para lanzar excepción
        mock_create_all.side_effect = Exception("Database connection failed")
        
        # Ejecutar función y verificar que lanza excepción
        with pytest.raises(Exception) as exc_info:
            init_db()
        
        assert "Database connection failed" in str(exc_info.value)
        mock_create_all.assert_called_once_with(bind=mock_engine)

    @patch('app.init_db.Base.metadata.create_all')
    @patch('app.init_db.engine')
    def test_init_db_prints_correct_messages(self, mock_engine, mock_create_all, capsys):
        """Test que init_db imprime los mensajes correctos"""
        # Configurar mock
        mock_engine.url = "postgresql://test:test@localhost/test"
        
        # Ejecutar función
        init_db()
        
        # Capturar output
        captured = capsys.readouterr()
        
        # Verificar mensajes
        assert "Creando tablas en la base de datos..." in captured.out
        assert "Conectando a: postgresql://test:test@localhost/test" in captured.out
        assert "Base de datos inicializada correctamente" in captured.out
        assert "Tablas creadas: videos, votes" in captured.out

    @patch('app.init_db.Base.metadata.create_all')
    @patch('app.init_db.engine')
    def test_init_db_with_none_url(self, mock_engine, mock_create_all):
        """Test que init_db maneja URL None"""
        # Configurar mock con URL None
        mock_engine.url = None
        
        # Ejecutar función
        init_db()
        
        # Verificar que se llamó create_all
        mock_create_all.assert_called_once_with(bind=mock_engine)

    @patch('app.init_db.Base.metadata.create_all')
    @patch('app.init_db.engine')
    def test_init_db_with_empty_url(self, mock_engine, mock_create_all):
        """Test que init_db maneja URL vacía"""
        # Configurar mock con URL vacía
        mock_engine.url = ""
        
        # Ejecutar función
        init_db()
        
        # Verificar que se llamó create_all
        mock_create_all.assert_called_once_with(bind=mock_engine)
