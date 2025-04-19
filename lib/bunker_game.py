import random
import discord
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
from io import BytesIO

from lib.ai_client import G4FClient

def weighed_random(tbl: List[Tuple[Any, float]]) -> Any:
    items = [x[0] for x in tbl]  # Элементы
    weights = [x[1] for x in tbl]  # Веса
    return random.choices(items, weights=weights, k=1)[0]

# Вынесем данные в отдельные константы в верхней части файла
class GameData:
    """Класс для хранения данных игры"""
    
    # Данные для генерации карточек игроков
    GENDERS = ["Мужчина", "Женщина"]
    
    BODY_TYPES = ["Худощавое", "Толстое", "Среднее", "Спортивное"]
    
    SKILL_LEVELS = [
        ("Начинающий", 0.4),      # 40% шанс
        ("Средний", 0.3),         # 30% шанс
        ("Профессионал", 0.2),    # 20% шанс
        ("Кандидат наук", 0.1)    # 10% шанс
    ]
    
    TRAITS = [
        "Трудолюбивый", "Ленивый", "Общительный", "Замкнутый", "Умный", "Глупый", 
        "Творческий", "Практичный", "Храбрый", "Трусливый", "Честный", "Лживый",
        "Оптимист", "Пессимист", "Щедрый", "Жадный", "Терпеливый", "Вспыльчивый",
        "Добрый", "Злой", "Внимательный", "Рассеянный", "Аккуратный", "Неряшливый",
        "Целеустремленный", "Безвольный", "Спокойный", "Нервный", "Веселый", "Угрюмый",
        "Любопытный", "Равнодушный", "Ответственный", "Безответственный", "Дружелюбный", "Агрессивный"
    ]
    
    PROFESSIONS = [
        "Врач", "Инженер", "Учитель", "Военный", "Фермер", "Программист", 
        "Повар", "Строитель", "Ученый", "Пилот", "Электрик", "Сантехник",
        "Психолог", "Биолог", "Химик", "Механик", "Сварщик", "Охотник"
    ]
    
    HEALTH_STATES = [
        ("Здоров", 0.3),  # 30% шанс
        ("Диабет", 0.05),  
        ("Астма", 0.05),         
        ("Аллергия", 0.05),      
        ("Болезнь сердца", 0.05),
        ("Проблемы со зрением", 0.05),
        ("Неизвестная болезнь", 0.05),
        ("Анемия", 0.05),
        ("Артрит", 0.05),
        ("Мигрень", 0.05),
        ("Депрессия", 0.05),
        ("Гипертония", 0.05),
        ("Язва желудка", 0.05),
        ("Бессонница", 0.05),
        ("Эпилепсия", 0.05)
    ]

    HEALTH_STAGES = [
        ("Лёгкое", 0.5),
        ("Среднее", 0.3),
        ("Тяжёлое", 0.2)
    ]
    
    HOBBIES = [
        "Рыбалка", "Садоводство", "Чтение", "Рисование", "Музыка", 
        "Спорт", "Готовка", "Фотография", "Шахматы", "Коллекционирование",
        "Туризм", "Охота", "Программирование", "Ремонт техники", "Вязание"
    ]
    
    PHOBIAS = [
        "Клаустрофобия", "Акрофобия (страх высоты)", "Арахнофобия (страх пауков)", 
        "Никтофобия (страх темноты)", "Аквафобия (страх воды)", "Агорафобия (страх открытых пространств)",
        "Айлурофобия (страх кошек)", "Гемофобия (страх крови)", "Кинофобия (страх собак)", 
        "Астрафобия (страх грозы)", "Социофобия (страх общения)", "Мизофобия (страх микробов)",
        "Танатофобия (страх смерти)", "Аэрофобия (страх полетов)", "Герпетофобия (страх рептилий)",
        "Апифобия (страх пчел)", "Трипанофобия (страх уколов)", "Ксенофобия (страх незнакомцев)",
        "Офидиофобия (страх змей)", "Монофобия (страх одиночества)"
    ]
    
    INVENTORY = [
        "Аптечка", "Набор инструментов", "AK-47", "Карта местности",
        "Спальный мешок", "Палатка", "Компас", "Огнетушитель", 
        "Солнечная батарея", "Фильтр для воды", "Газовая горелка", "Бинокль",
        "Дизельный генератор", "Запас топлива", "Сварочный аппарат", "Токарный станок",
        "Мотоцикл", "Квадрокоптер", "Спутниковый телефон", "Радиостанция",
        "Промышленный холодильник", "Система гидропоники", "Инкубатор для яиц",
        "Промышленная стиральная машина", "Дистиллятор воды", "Ветрогенератор",
        "Промышленная печь", "Медицинское оборудование", "Микроскоп", "Телескоп",
        "Сейф", "Верстак с инструментами", "Швейная машинка", "3D-принтер",
        "Лодка", "Снегоход", "Переносная теплица", "Мини-трактор",
        "Токарный станок", "Фрезерный станок", "Сушильный шкаф"
    ]
    
    BACKPACK_ITEMS = [
        "Нож", "Спички", "Фляга с водой", "Консервы", "Батарейки",
        "Свечи", "Блокнот и ручка", "Антисептик", "Зажигалка", "Рыболовные снасти",
        "Сухой паек", "Радиоприемник", "Часы", "Кофе", "Чай", "Шоколад", "Веревка",
        "Фонарик", "Компас", "Карта", "Аптечка первой помощи", "Мультитул",
        "Спальный мешок", "Термос", "Солнцезащитные очки", "Репеллент от насекомых",
        "Зубная щетка и паста", "Мыло", "Полотенце", "Теплая одежда", "Дождевик",
        "Перчатки", "Бинокль", "Сигнальная ракета", "Таблетки для очистки воды",
        "Швейный набор", "Скотч", "Зарядное устройство", "Портативный аккумулятор",
        "Спутниковый телефон", "Солнечная зарядка", "Рация", "Топор", "Лопата",
        "Котелок", "Фильтр для воды", "Спички в водонепроницаемой упаковке",
        "Сухое горючее", "Марля", "Бинты", "Антибиотики", "Обезболивающее",
        "Противоаллергенные препараты", "Активированный уголь", "Витамины"
    ]
    
    ADDITIONAL_INFO = [
        # Навыки выживания
        "Умеет разводить огонь без спичек", "Знает съедобные растения", "Умеет ставить ловушки",
        "Имеет опыт выживания в дикой природе", "Умеет очищать воду", "Знает основы первой помощи",
        
        # Практические навыки
        "Умеет шить одежду", "Хорошо готовит", "Умеет консервировать продукты",
        "Разбирается в электрике", "Умеет ремонтировать технику", "Знает основы строительства",
        "Умеет варить мыло", "Умеет делать свечи", "Умеет выращивать растения",
        
        # Интеллектуальные навыки
        "Знает несколько иностранных языков", "Разбирается в медицине", "Имеет фотографическую память",
        "Эксперт по криптографии", "Знает высшую математику", "Разбирается в химии",
        
        # Социальные навыки
        "Хороший лидер", "Умеет разрешать конфликты", "Отличный рассказчик",
        "Умеет поднять боевой дух", "Хорошо работает в команде", "Умеет вести переговоры",
        
        # Творческие навыки
        "Умеет играть на нескольких музыкальных инструментах", "Талантливый художник",
        "Пишет стихи и песни", "Умеет танцевать", "Хороший актер", "Умеет делать скульптуры",
        
        # Необычные навыки
        "Умеет читать по губам", "Владеет языком жестов", "Разбирается в астрономии",
        "Умеет предсказывать погоду", "Хорошо ориентируется по звездам", "Умеет гипнотизировать",
        
        # Полезные знания
        "Знает все о грибах и ягодах", "Разбирается в лекарственных травах",
        "Умеет делать самогон", "Знает как делать порох", "Умеет обращаться с любым оружием",
        "Эксперт по системам безопасности"
    ]
    
    SPECIAL_ABILITIES = [
        "Может улучшить здоровье у выбранного игрока на 1 ступень",
        "Может ухудшить здоровье у выбранного игрока на 1 ступень",
        "Может поменять пол у выбранного игрока на противоположный",
        "Может получить новый случайный предмет в свой инвентарь",
        "Может получить новый случайный предмет в свой рюкзак",
        "Может расширить бункер на 30 кв.м",
        "Может открыть одну характеристику другого игрока",
        "Может заставить показать всех игроков одну характеристику",
        "Может украсть одну вещь из рюкзака другого игрока",
        "Может украсть одну вещь из инвентаря другого игрока",
        "Может поменяться одной характеристикой с другим игроком", # Выбор игрока и характеристики
    ]
    
    # Данные для генерации бункера
    BUNKER_SIZES = ["Маленький (30 кв.м)", "Средний (60 кв.м)", "Большой (100 кв.м)", "Огромный (150 кв.м)"]
    BUNKER_DURATIONS = ["6 месяцев", "1 год", "2 года", "3 года", "5 лет", "10 лет"]
    FOOD_SUPPLIES = [
        "Еды нет", "Очень мало еды (на месяц)", "Мало еды (на полгода)", 
        "Достаточно еды (на 2 года)", "Много еды (на 4 года)"
    ]
    BUNKER_ITEMS = [
        # Полезные предметы
        "Медицинское оборудование", "Система фильтрации воды", "Система очистки воздуха",
        "Генератор электричества", "Оружейная комната", "Библиотека", "Лаборатория",
        "Теплица для выращивания растений", "Радиооборудование", "Компьютерное оборудование",
        "Запас медикаментов", "Мастерская", "Инструменты для ремонта", "Запчасти для техники",
        
        # Развлечения и досуг
        "Коллекция настольных игр", "Музыкальные инструменты", "Спортивный инвентарь",
        "Художественные принадлежности", "Домашний кинотеатр", "Караоке-система",
        
        # Сомнительная польза
        "Коллекция редких марок", "Чучело медведя", "Статуя Давида в полный рост",
        "Аквариум с экзотическими рыбками", "Коллекция бабочек", "Старый пинбольный автомат",
        
        # Потенциально опасные
        "Экспериментальные химикаты", "Нестабильный реактор", "Контейнер с неизвестным вирусом",
        "Взрывоопасные материалы", "Радиоактивные элементы", "Ядовитые растения в горшках",
        
        # Странные и бесполезные
        "Чемодан с париками", "Коллекция резиновых уточек", "Сломанный факс",
        "Стопка журналов 1980-х годов", "Чучело единорога", "Машина для производства мыльных пузырей"
    ]


class Player:
    """Класс, представляющий игрока в игре Бункер"""
    
    def __init__(self, id: int, name: str):
        """
        Инициализация игрока
        
        Args:
            id: Идентификатор игрока
            name: Имя игрока
        """
        self.id = id
        self.name = name
        self.message_id = None
        self.status_message_id = None
        
        # Характеристики персонажа
        self.gender = ""
        self.body_type = ""
        self.trait = ""
        self.profession = ""
        self.health = ""
        self.hobby = ""
        self.phobia = ""
        self.inventory = ""
        self.backpack = ""
        self.additional = ""
        self.special_ability = ""
        
        # Открытые характеристики
        self.revealed_attributes = {
            "gender": False,
            "body": False,
            "trait": False,
            "profession": False,
            "health": False,
            "hobby": False,
            "phobia": False,
            "inventory": False,
            "backpack": False,
            "additional": False
        }
        
        # Активен ли игрок (не выбыл из игры)
        self.is_active = True
    
    async def generate_character(self, ai_client: G4FClient) -> None:
        """Генерация случайных характеристик персонажа"""
        self.gender = random.choice(GameData.GENDERS)

        # Генерация телосложения
        body_type = random.choice(GameData.BODY_TYPES)
        body_height = int(np.random.normal(180, 15))  # Mean=180, std=15 gives most heights between 150-210
        body_height = max(150, min(210, body_height))  # Clamp between 150-210 cm
        self.body_type = f"{body_type} ({body_height} см)"
        self.trait = random.choice(GameData.TRAITS)
        
        # Генерация профессии с уровнем
        profession = random.choice(GameData.PROFESSIONS)
        profession_level = weighed_random(GameData.SKILL_LEVELS)
        self.profession = f"{profession} ({profession_level})"
        
        # Генерация здоровья
        health = weighed_random(GameData.HEALTH_STATES)
        health_stage = weighed_random(GameData.HEALTH_STAGES)
        if health != "Здоров":
            self.health = f"{health} ({health_stage})"
        else:
            self.health = health
        
        # Генерация хобби с уровнем
        hobby = random.choice(GameData.HOBBIES)
        hobby_level = weighed_random(GameData.SKILL_LEVELS)
        self.hobby = f"{hobby} ({hobby_level})"
        
        self.phobia = random.choice(GameData.PHOBIAS)
        self.inventory = random.choice(GameData.INVENTORY)
        
        # Генерация от 1 до 3 предметов для рюкзака
        backpack_items_count = random.randint(1, 3)
        backpack_items = random.sample(GameData.BACKPACK_ITEMS, k=backpack_items_count)
        self.backpack = ", ".join(backpack_items)
        
        self.additional = random.choice(GameData.ADDITIONAL_INFO)

        # Генерация специальной возможности
        if random.random() < 0.35:
            self.special_ability = random.choice(GameData.SPECIAL_ABILITIES)
        else:
            self.special_ability = ""

        self.description = ""
        self.description = await ai_client.generate_message([
            {"role": "system", "content": "You are a helpful assistant that generates character descriptions for a bunker game. Always respond in User language."},
            {"role": "user", "content": f"Сгенерируй краткую биографию для персонажа. В ответе оставь только само описание, не пиши ничего от своего имени. В биографию так-же включи: Имя, цвет глаз, цвет волос, цвет кожи. Сгенерируй биографию от лица персонажа. Сгенерируй всё одним предложением. Вот досье персонажа: {self.get_character_card()}"}
        ])
    
    def get_character_card(self) -> str:
        """
        Получение форматированной карточки персонажа
        
        Returns:
            str: Форматированное описание персонажа
        """
        return (
            f"Вы: {self.description}\n"
            f"**Пол**: {self.gender}\n"
            f"**Телосложение**: {self.body_type}\n"
            f"**Человеческая черта**: {self.trait}\n"
            f"**Профессия**: {self.profession}\n"
            f"**Здоровье**: {self.health}\n"
            f"**Хобби / Увлечение**: {self.hobby}\n"
            f"**Фобия / Страх**: {self.phobia}\n"
            f"**Крупный инвентарь**: {self.inventory}\n"
            f"**Рюкзак**: {self.backpack}\n"
            f"**Дополнительное сведение**: {self.additional}\n"
            f"**Спец. возможность**: {self.special_ability}"
        )
    
    def reveal_attribute(self, attribute: str) -> bool:
        """
        Раскрыть характеристику персонажа
        
        Args:
            attribute: Имя атрибута для раскрытия
            
        Returns:
            bool: True, если атрибут успешно раскрыт, False, если уже был раскрыт
        """
        if not self.revealed_attributes.get(attribute, False):
            self.revealed_attributes[attribute] = True
            return True
        return False
    
    def get_revealed_attribute(self, attribute: str) -> Optional[str]:
        """
        Получить раскрытую характеристику или None, если она закрыта
        
        Args:
            attribute: Имя атрибута
            
        Returns:
            Optional[str]: Значение атрибута или None, если не раскрыт
        """
        if self.revealed_attributes.get(attribute, False):
            attribute_map = {
                "gender": self.gender,
                "body": self.body_type,
                "trait": self.trait,
                "profession": self.profession,
                "health": self.health,
                "hobby": self.hobby,
                "phobia": self.phobia,
                "inventory": self.inventory,
                "backpack": self.backpack,
                "additional": self.additional
            }
            return attribute_map.get(attribute)
        return None


class Bunker:
    """Класс, представляющий бункер в игре"""
    
    def __init__(self, ai_client: G4FClient):
        """Инициализация бункера"""
        self.ai_client = ai_client
        self.size = ""
        self.duration = ""
        self.food = ""
        self.items = []
    
    def generate(self) -> None:
        """Генерация случайного бункера"""
        self.size = random.choice(GameData.BUNKER_SIZES)
        self.duration = random.choice(GameData.BUNKER_DURATIONS)
        self.food = random.choice(GameData.FOOD_SUPPLIES)
        # Выбираем от 2 до 5 случайных предметов
        self.items = random.sample(GameData.BUNKER_ITEMS, k=random.randint(1, 5))
    
    async def get_description(self) -> str:
        """
        Получение форматированного описания бункера
        
        Returns:
            str: Форматированное описание бункера
        """
        items_str = ", ".join(self.items)

        bunker_disaster = await self.ai_client.generate_message([
            {"role": "system", "content": "You are a helpful assistant that generates bunker disaster descriptions for a bunker game. Always respond in User language."},
            {"role": "user", "content": f"Сгенерируй случайный смертельный катаклизм для игры в бункер (Например вирус, наводнение, захват пришельцами и тд (придумай)). Катаклизм - это то что происходит за пределами бункера! В зависимости от этого игроки будут выбирать кто заслуживает место в бункере. В ответе оставь только само описание, не пиши ничего от своего имени. В ответе укажи название катаклизма, его описание и последствия."}
        ])
        
        return (
            "**Описание найденного бункера**\n\n"
            f"{bunker_disaster}\n\n"
            f"**Размер бункера**: {self.size}\n"
            f"**Время нахождения**: {self.duration}\n"
            f"**Количество еды**: {self.food}\n"
            f"**В бункере имеется**: {items_str}\n\n"
            "В зависимости от того, что находится в бункере, вам предстоит определить, "
            "кто из выживших будет более полезен, учитывая данные обстоятельства."
        )


class ImageGenerator:
    """Класс для генерации изображений статуса игры"""
    
    @staticmethod
    def wrap_text(text: str, max_width: int, font) -> Tuple[List[str], int]:
        """
        Переносит текст по строкам, чтобы он вписывался в заданную ширину
        
        Args:
            text: Текст для переноса
            max_width: Максимальная ширина строки
            font: Шрифт для расчета ширины
            
        Returns:
            Tuple[List[str], int]: Список строк и высота текста
        """
        lines = []
        words = str(text).split()
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            # Используем getbbox вместо getlength для лучшей совместимости
            width = font.getbbox(test_line)[2] if hasattr(font, 'getbbox') else font.getsize(test_line)[0]
            
            if width <= max_width:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Используем getbbox или getsize в зависимости от доступности метода
        line_height = (font.getbbox('A')[3] if hasattr(font, 'getbbox') else font.getsize('A')[1]) + 4
        total_height = len(lines) * line_height
        return lines, total_height
    
    @staticmethod
    def generate_status_image(players: List[Player]) -> discord.File:
        """
        Генерация изображения с таблицей статусов игроков
        
        Args:
            players: Список игроков
            
        Returns:
            discord.File: Файл с изображением таблицы статусов
        """
        try:
            # Фильтруем только активных игроков
            active_players = [p for p in players if p.is_active]
            
            # Определяем шрифты и цвета
            font_path = os.path.join(os.path.dirname(__file__), 'fonts/arial.ttf')
            if not os.path.exists(font_path):
                # Пробуем различные распространенные пути к шрифтам
                possible_paths = [
                    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",  # Linux
                    "/usr/share/fonts/TTF/Arial.ttf",                   # Arch Linux
                    "C:/Windows/Fonts/arial.ttf",                       # Windows
                    "/System/Library/Fonts/Arial.ttf"                   # macOS
                ]
                
                for path in possible_paths:
                    if os.path.exists(path):
                        font_path = path
                        break
                else:
                    # Если ничего не найдено, используем стандартный шрифт
                    header_font = ImageFont.load_default()
                    cell_font = ImageFont.load_default()
                    font_path = "default"
            
            if font_path != "default":
                try:
                    header_font = ImageFont.truetype(font_path, 16)
                    cell_font = ImageFont.truetype(font_path, 14)
                except:
                    header_font = ImageFont.load_default()
                    cell_font = ImageFont.load_default()
            
            # Определяем колонки и их базовые ширины
            columns = ["Игрок", "Пол", "Тело", "Черта", "Проф.", "Здоровье", "Хобби", "Фобия", "Инв.", "Рюкзак", "Доп."]
            column_widths = [150, 80, 100, 100, 100, 100, 100, 100, 100, 100, 100]
            
            # Рассчитываем размеры изображения
            padding = 10
            header_height = 40
            min_cell_height = 30  # Минимальная высота ячейки
            
            # Подготавливаем данные игроков и рассчитываем необходимую высоту для каждого ряда
            player_data_rows = []
            row_heights = []
            
            for player in active_players:
                # Получаем данные игрока
                player_data = [
                    player.name,
                    player.get_revealed_attribute("gender") or "?",
                    player.get_revealed_attribute("body") or "?",
                    player.get_revealed_attribute("trait") or "?",
                    player.get_revealed_attribute("profession") or "?",
                    player.get_revealed_attribute("health") or "?",
                    player.get_revealed_attribute("hobby") or "?",
                    player.get_revealed_attribute("phobia") or "?",
                    player.get_revealed_attribute("inventory") or "?",
                    player.get_revealed_attribute("backpack") or "?",
                    player.get_revealed_attribute("additional") or "?"
                ]
                player_data_rows.append(player_data)
                
                # Рассчитываем максимальную высоту ячеек в ряду
                max_height = min_cell_height
                for i, data in enumerate(player_data):
                    lines, height = ImageGenerator.wrap_text(data, column_widths[i] - 10, cell_font)
                    max_height = max(max_height, height + 10)  # Добавляем отступ
                
                row_heights.append(max_height)
            
            # Общая ширина изображения
            width = sum(column_widths) + padding * 2
            # Общая высота изображения
            height = header_height + sum(row_heights) + padding * 2
            
            # Создаем изображение
            image = Image.new('RGB', (width, height), color=(255, 255, 255))
            draw = ImageDraw.Draw(image)
            
            # Рисуем заголовок
            x = padding
            y = padding
            
            for i, column in enumerate(columns):
                # Рисуем ячейку заголовка
                draw.rectangle(
                    (x, y, x + column_widths[i], y + header_height),
                    outline=(0, 0, 0),
                    fill=(200, 200, 200)
                )
                
                # Центрируем текст заголовка
                if hasattr(header_font, 'getbbox'):
                    text_width = header_font.getbbox(column)[2]
                    text_height = header_font.getbbox(column)[3]
                else:
                    text_width, text_height = header_font.getsize(column)
                
                text_x = x + (column_widths[i] - text_width) / 2
                text_y = y + (header_height - text_height) / 2
                
                draw.text((text_x, text_y), column, font=header_font, fill=(0, 0, 0))
                
                x += column_widths[i]
            
            # Рисуем данные игроков
            current_y = padding + header_height
            
            for row, (player_data, row_height) in enumerate(zip(player_data_rows, row_heights)):
                x = padding
                
                for i, data in enumerate(player_data):
                    # Рисуем ячейку
                    cell_color = (230, 230, 230) if row % 2 == 0 else (255, 255, 255)
                    
                    draw.rectangle(
                        (x, current_y, x + column_widths[i], current_y + row_height),
                        outline=(0, 0, 0),
                        fill=cell_color
                    )
                    
                    # Делаем перенос текста и отрисовываем его
                    lines, _ = ImageGenerator.wrap_text(data, column_widths[i] - 10, cell_font)
                    line_height = (cell_font.getbbox('A')[3] if hasattr(cell_font, 'getbbox') else cell_font.getsize('A')[1]) + 4
                    
                    # Рассчитываем вертикальный отступ, чтобы текст был по центру вертикально
                    total_text_height = len(lines) * line_height
                    y_offset = (row_height - total_text_height) / 2
                    
                    for j, line in enumerate(lines):
                        line_y = current_y + y_offset + j * line_height
                        draw.text((x + 5, line_y), line, font=cell_font, fill=(0, 0, 0))
                    
                    x += column_widths[i]
                
                current_y += row_height
            
            # Сохраняем изображение в байты
            image_bytes = BytesIO()
            image.save(image_bytes, format='PNG')
            image_bytes.seek(0)
            
            return discord.File(image_bytes, filename='status.png')
        
        except Exception as e:
            print(f"Ошибка при создании изображения: {e}")
            # Создаем простое изображение с сообщением об ошибке
            error_image = Image.new('RGB', (400, 100), color=(255, 255, 255))
            draw = ImageDraw.Draw(error_image)
            
            try:
                font = ImageFont.load_default()
                draw.text((10, 10), f"Ошибка создания изображения: {str(e)[:50]}", font=font, fill=(255, 0, 0))
            except:
                draw.text((10, 10), "Ошибка создания изображения", fill=(255, 0, 0))
            
            # Сохраняем изображение ошибки в байты
            error_bytes = BytesIO()
            error_image.save(error_bytes, format='PNG')
            error_bytes.seek(0)
            
            return discord.File(error_bytes, filename='error.png')


class BunkerGame:
    """Класс, управляющий игровой логикой"""
    
    def __init__(self, ai_client: G4FClient, admin_id: int, channel_id: int):
        """
        Инициализация игры
        
        Args:
            admin_id: ID администратора игры
            channel_id: ID канала, в котором проходит игра
        """
        self.ai_client = ai_client

        self.admin_id = admin_id
        self.channel_id = channel_id
        self.message_id = None
        self.admin_message_id = None
        self.vote_message_id = None
        self.status = "waiting"  # waiting, running, finished
        self.players: List[Player] = []
        self.bunker = Bunker(self.ai_client)
        self.current_round = 0
        self.votes = {}  # {voter_id: voted_for_id}
        self.voted_players = set()  # Множество ID проголосовавших игроков
        self.active_voting_players = 0  # Счетчик активных игроков для голосования
    
    def add_player(self, player: Player) -> None:
        """
        Добавить игрока в игру
        
        Args:
            player: Объект игрока
        """
        self.players.append(player)
    
    def remove_player(self, player_id: int) -> bool:
        """
        Убрать игрока из игры
        
        Args:
            player_id: ID игрока для удаления
            
        Returns:
            bool: True, если игрок успешно удален, False, если игрок не найден
        """
        for player in self.players:
            if player.id == player_id:
                player.is_active = False
                return True
        return False
    
    def generate_bunker(self) -> None:
        """Генерация бункера"""
        self.bunker.generate()
    
    async def generate_player_cards(self) -> None:
        """Генерация карточек для всех игроков"""
        for player in self.players:
            await player.generate_character(self.ai_client)
    
    def generate_status_image(self) -> discord.File:
        """
        Генерация изображения с таблицей статусов
        
        Returns:
            discord.File: Файл с изображением таблицы статусов
        """
        return ImageGenerator.generate_status_image(self.players)
    
    async def update_all_player_tables(self, bot) -> None:
        """
        Обновление таблиц статусов для всех игроков
        
        Args:
            bot: Объект бота Discord
        """
        try:
            # Генерируем изображение для каждого игрока отдельно
            for player in self.players:
                if not player.is_active:
                    continue
                
                user = bot.get_user(player.id)
                if not user:
                    continue
                
                try:
                    # Создаем новое изображение для каждого игрока
                    status_image = self.generate_status_image()
                    
                    dm_channel = await user.create_dm()
                    
                    if player.status_message_id:
                        try:
                            message = await dm_channel.fetch_message(player.status_message_id)
                            await message.delete()
                        except:
                            pass
                    
                    message = await dm_channel.send(file=status_image)
                    player.status_message_id = message.id
                except Exception as e:
                    print(f"Ошибка при обновлении таблицы для игрока {player.name}: {e}")
        except Exception as e:
            print(f"Ошибка при обновлении таблиц: {e}")
    
    def next_round(self) -> int:
        """
        Переход к следующему раунду
        
        Returns:
            int: Номер нового раунда
        """
        self.current_round += 1
        return self.current_round
    
    def get_active_players(self) -> List[Player]:
        """
        Получение списка активных игроков
        
        Returns:
            List[Player]: Список активных игроков
        """
        return [player for player in self.players if player.is_active]
    
    def get_player_by_id(self, player_id: int) -> Optional[Player]:
        """
        Получение игрока по ID
        
        Args:
            player_id: ID игрока
            
        Returns:
            Optional[Player]: Объект игрока или None, если игрок не найден
        """
        for player in self.players:
            if player.id == player_id:
                return player
        return None
    
    def reset_votes(self) -> None:
        """Сброс голосов"""
        self.votes = {}
        self.voted_players = set()
    
    def add_vote(self, voter_id: int, target_id: int) -> bool:
        """
        Добавление голоса
        
        Args:
            voter_id: ID голосующего игрока
            target_id: ID игрока, за которого голосуют
            
        Returns:
            bool: True, если голос успешно учтен, False, если игрок уже голосовал
        """
        if voter_id in self.voted_players:
            return False
        
        self.votes[voter_id] = target_id
        self.voted_players.add(voter_id)
        return True
    
    def count_votes(self) -> Dict[int, int]:
        """
        Подсчет голосов
        
        Returns:
            Dict[int, int]: Словарь {ID игрока: количество голосов}
        """
        results = {}
        for target_id in self.votes.values():
            results[target_id] = results.get(target_id, 0) + 1
        return results 