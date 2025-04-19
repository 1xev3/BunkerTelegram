import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging():
    """Настройка логирования"""
    # Создание директории для логов, если её нет
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Настройка корневого логгера
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Форматирование логов
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Файловый обработчик для всех сообщений
    file_handler = RotatingFileHandler(
        'logs/bunker_bot.log',
        maxBytes=10*1024*1024,  # 10 МБ
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    
    # Файловый обработчик только для ошибок
    error_handler = RotatingFileHandler(
        'logs/errors.log',
        maxBytes=10*1024*1024,  # 10 МБ
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    
    # Консольный обработчик
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Добавление обработчиков к логгеру
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)
    
    # Настройка логгера для discord.py
    discord_logger = logging.getLogger('discord')
    discord_logger.setLevel(logging.INFO)
    
    # Отключение логирования для других модулей
    logging.getLogger('discord.http').setLevel(logging.WARNING)
    logging.getLogger('discord.gateway').setLevel(logging.WARNING)
    
    return logger 