"""config.py - Общие настройки и логгер для всего пакета"""

import sys, os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any

SERVER_MESSAGE = 25
logging.addLevelName(SERVER_MESSAGE, "SERVER_MESSAGE")


class Config:
    """Класс для хранения общих настроек и логгера"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, config_filename: str = "config.yaml"): 
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config_filename = config_filename
        return cls._instance
    
    def __init__(self, config_filename: str = "config.yaml"):
        if not self._initialized:
            self.CONFIG_FILENAME = config_filename
            self._load_config()
            self._setup_logger()
            self._initialized = True
    
    def _load_config(self):
        """Загружает конфигурацию из YAML файла"""
        # Ищем конфиг в нескольких местах
        possible_paths = [
            str(f"{Path(__file__).resolve().parent.parent.parent}{os.sep}{self.CONFIG_FILENAME}"),
            str(f"{Path(__file__).resolve().parent}{os.sep}{self.CONFIG_FILENAME}"),
            str(f"{Path.cwd()}{os.sep}{self.CONFIG_FILENAME}"),
            self.CONFIG_FILENAME
        ]
        
        config_loaded = False
        for config_path in possible_paths:
            try:
                with open(config_path, 'r', encoding='utf-8') as file:
                    config_data = yaml.safe_load(file)
                
                required_sections = ['server', 'auth', 'cache', 'download']
                for section in required_sections:
                    if section not in config_data:
                        raise ValueError(f"Отсутствует обязательная секция '{section}' в конфигурации")
                
                self.base_url = config_data['server'].get('base_url', '').rstrip('/')
                self.base_path = config_data['server'].get('base_path', '').strip('/')
                self.api_token = config_data['auth'].get('api_token', '')
                self.cache_enabled = bool(config_data['cache'].get('use_cache', True))
                self.cache_dir = str(Path(config_path).parent / config_data['cache'].get('cache_dir', './cache'))
                self.timeout = config_data['download'].get('timeout', 30)
                self.show_progress = config_data['download'].get('show_progress', True)
                self.chunk_size = int(config_data['download'].get('chunk_size', 8192))
                self.verify_ssl = config_data['server'].get('verify_ssl', True)
                cache_max_str = config_data['cache'].get('cache_max', '0')
                self.cache_max_bytes = self._parse_cache_size(cache_max_str)
                
                log_level_str = config_data.get('logging', {}).get('console_level', 'INFO').upper()
                self.verbose_stats = bool(config_data.get('logging', {}).get('verbose_stats', True))
                self.log_level = getattr(logging, log_level_str, logging.INFO)
                self.show_server_messages = (log_level_str == "INFO")
                
                config_loaded = True
                #print(f"Config loaded from: {config_path}")
                break
                
            except (FileNotFoundError, yaml.YAMLError, ValueError, OSError) as e:
                continue
        
        if not config_loaded:
            print(f"❌ Не удалось загрузить конфигурационный файл: {self.CONFIG_FILENAME}")
            sys.exit(1)
    
    def _parse_cache_size(self, size_str: str) -> int:
        """Парсит строку с размером кэша"""
        import re
        
        if not size_str or size_str == "0":
            return 0
        
        size_str = size_str.lower().replace(" ", "")
        pattern = r'^(\d+(?:\.\d+)?)([kmgt]?b)$'
        match = re.match(pattern, size_str)
        
        if not match:
            print(f"❌ Неверный формат размера кэша: {size_str}. Используйте '500MB', '1GB', '100KB'")
            sys.exit(1)
        
        size_value = float(match.group(1))
        unit = match.group(2)
        
        units = {
            'b': 1,
            'kb': 1024,
            'mb': 1024 ** 2,
            'gb': 1024 ** 3,
            'tb': 1024 ** 4
        }
        
        if unit not in units:
            print(f"❌ Неизвестная единица измерения: {unit}")
            sys.exit(1)
        
        return int(size_value * units[unit])
    
    def _setup_logger(self):
        """Настраивает логгер"""
        self.logger = logging.getLogger('mephistdatakit')
        self.logger.setLevel(self.log_level)
        self.logger.handlers.clear()
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        
        class EmojiFormatter(logging.Formatter):
            def format(self, record):
                if record.levelno >= logging.ERROR:
                    record.emoji = "❌ "
                elif record.levelno >= logging.WARNING:
                    record.emoji = "⚠️ "
                elif record.levelno == SERVER_MESSAGE:
                    record.emoji = "💬 "
                elif record.levelno >= logging.INFO:
                    record.emoji = "✅ "
                else:
                    record.emoji = "ℹ️ "
                return super().format(record)
        
        formatter = EmojiFormatter('%(emoji)s %(message)s')
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def get_logger(self, name: str = None) -> logging.Logger:
        """Возвращает логгер для конкретного модуля"""
        if name:
            return logging.getLogger(f'mephistdatakit.{name}')
        return self.logger
    
    def get_session_config(self) -> Dict[str, Any]:
        """Возвращает конфигурацию для сессии"""
        return {
            'base_url': self.base_url,
            'base_path': self.base_path,
            'api_token': self.api_token,
            'verify_ssl': self.verify_ssl,
            'timeout': self.timeout
        }