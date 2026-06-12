"""
MephistDataKit - Framework for MEPhIST tokamak data analysis
"""

# Указание корректной версии важно, так как на сервере идёт проверка
# актуальности версии клиента. При создании нового релиза надо
# ручками поправить версию
__version__ = "2025.01.2"
__author__ = "MEPhIST Team"

from .client import Client
from .shot import Shot

__all__ = ['client', 'Client', 'shot', 'Shot', 'config', 'common', 'mw_interferometry']

