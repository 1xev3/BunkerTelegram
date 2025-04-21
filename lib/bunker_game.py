import random
import discord
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
from io import BytesIO
import logging
import re

from lib.ai_client import G4FClient
from lib.game_data import GameData

def weighed_random(tbl: List[Tuple[Any, float]]) -> Any:
    items = [x[0] for x in tbl]  # Элементы
    weights = [x[1] for x in tbl]  # Веса
    return random.choices(items, weights=weights, k=1)[0]

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
        self.body = ""
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

        # Генерация пола
        gender = weighed_random(GameData.GENDERS)
        gender_affix = weighed_random(GameData.GENDER_AFFIXES)
        years_old = weighed_random(GameData.AGES)
        years_old = random.randint(years_old[0], years_old[1])
        self.gender = f"{gender} {gender_affix} ({years_old} лет)"

        # Генерация телосложения
        body = weighed_random(GameData.BODY_TYPES)
        
        # Генерация роста в зависимости от возраста
        if years_old < 18:
            # Для подростков: средний рост с большим разбросом
            body_height = int(np.random.normal(160, 20))
        elif years_old < 30:
            # Для молодых взрослых: высокий средний рост
            body_height = int(np.random.normal(180, 15))
        elif years_old < 50:
            # Для среднего возраста: средний рост
            body_height = int(np.random.normal(175, 10))
        else:
            # Для пожилых: немного ниже среднего роста
            body_height = int(np.random.normal(170, 8))
        
        # Корректировка роста в зависимости от пола
        if gender == "Женщина":
            body_height -= 10  # В среднем женщины ниже мужчин на 10 см
        
        # Ограничение роста разумными пределами
        body_height = max(150, min(210, body_height))
        self.body = f"{body} ({body_height} см)"
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
        backpack_items_count = random.randint(1, GameData.BACKPACK_ITEMS_COUNT_MAX)
        backpack_items = random.sample(GameData.BACKPACK_ITEMS, k=backpack_items_count)
        backpack_items_values = []
        for item in backpack_items:
            if isinstance(item, tuple):
                item_name, item_min, item_max = item
                item_count = random.randint(item_min, item_max)
                item_name = f"{item_name} ({item_count} шт)"
                backpack_items_values.append(item_name)
            else:
                backpack_items_values.append(item)
        self.backpack = ", ".join(backpack_items_values)
        
        self.additional = random.choice(GameData.ADDITIONAL_INFO)

        # Генерация специальной возможности
        if random.random() < GameData.SPECIAL_ABILITIES_CHANCE:
            self.special_ability = random.choice(GameData.SPECIAL_ABILITIES)
        else:
            self.special_ability = ""

        self.description = ""
        self.description = await ai_client.generate_message([
            {"role": "system", "content": "You are a helpful assistant that generates character descriptions for a bunker game. Always respond in User language."},
            {"role": "user", "content": f"""Сгенерируй краткое внешнее описание для персонажа. 
В ответе оставь только само описание, не пиши ничего от своего имени.
Придумай для персонажа: Имя, цвет глаз, цвет волос, стиль причёски, цвет кожи, стиль одежды, цвета одежды
Вот досье персонажа, которого нужно сгенерировать (исходя из него, придумывай): {self.get_character_card()}"""}])
    
    def get_formatted_attribute(self, attribute: str) -> str:
        """
        Получение форматированной характеристики персонажа
        
        Args:
            attribute: Имя характеристики
        """

        revealed_attr = self.get_revealed_attribute(attribute)
        if revealed_attr:
            return f"`~~{revealed_attr}~~`"
        else:
            return getattr(self, attribute, "err")

    def get_character_card(self) -> str:
        """
        Получение форматированной карточки персонажа
        
        Returns:
            str: Форматированное описание персонажа
        """
        return (
            f"{self.description}\n\n"
            f"> **Пол**: {self.get_formatted_attribute('gender')}\n"
            f"> **Телосложение**: {self.get_formatted_attribute('body')}\n"
            f"> **Человеческая черта**: {self.get_formatted_attribute('trait')}\n"
            f"> **Профессия**: {self.get_formatted_attribute('profession')}\n"
            f"> **Здоровье**: {self.get_formatted_attribute('health')}\n"
            f"> **Хобби / Увлечение**: {self.get_formatted_attribute('hobby')}\n"
            f"> **Фобия / Страх**: {self.get_formatted_attribute('phobia')}\n"
            f"> **Крупный инвентарь**: {self.get_formatted_attribute('inventory')}\n"
            f"> **Рюкзак**: {self.get_formatted_attribute('backpack')}\n"
            f"> **Дополнительное сведение**: {self.get_formatted_attribute('additional')}\n"
            f"> **Спец. возможность**: {self.get_formatted_attribute('special_ability')}"
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
            # attribute_map = {
            #     "gender": self.gender,
            #     "body": self.body_type,
            #     "trait": self.trait,
            #     "profession": self.profession,
            #     "health": self.health,
            #     "hobby": self.hobby,
            #     "phobia": self.phobia,
            #     "inventory": self.inventory,
            #     "backpack": self.backpack,
            #     "additional": self.additional
            # }
            return getattr(self, attribute, "err") #attribute_map.get(attribute)
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
        self.image = None  # Сохраняем PIL Image вместо URL
    
    async def generate(self):
        """Генерация случайного бункера"""
        self.theme = random.choice(GameData.BUNKER_THEMES)
        self.size = random.choice(GameData.BUNKER_SIZES)
        self.duration = random.choice(GameData.BUNKER_DURATIONS)
        self.food = random.choice(GameData.FOOD_SUPPLIES)
        # Выбираем от 2 до 5 случайных предметов
        self.items = random.sample(GameData.BUNKER_ITEMS, k=random.randint(1, GameData.BUNKER_ITEMS_COUNT_MAX))
        items_str = ", ".join(self.items)

        yield "Генерирую катаклизм..."
        self.disaster_info = await self.ai_client.generate_message([
            {"role": "system", "content": "You are a helpful assistant that generates bunker disaster descriptions for a bunker game. Always respond in User language."},
            {"role": "user", "content": f"""Сгенерируй случайный смертельный катаклизм для игры в\
бункер на тему: {self.theme}. 
Катаклизм - это то что происходит за пределами бункера! Не упоминай бункер в описании катаклизма.
В зависимости от этого игроки будут выбирать кто заслуживает место в бункере. 
В ответе оставь только само описание, не пиши ничего от своего имени. 
В ответе укажи название катаклизма, его описание и с чём предстоит столкнуться вне бункера."""}])
        
        yield "Генерирую описание бункера..."
        self.bunker_info = await self.ai_client.generate_message([
            {"role": "system", "content": "You are description generator for a bunker game. Always respond in User language."},
            {"role": "user", "content": f"""Сгенерируй краткое описание бункера по его характеристикам. Придумай какие комнаты в нём есть (в зависимости от размера и предметов в нём).
В ответе оставь только само описание, не пиши ничего от своего имени. 
Вот характеристики бункера: 
Размер: {self.size}
Еда: {self.food}
Предметы: {items_str}
"""}])

        # Генерация изображения бункера
        if GameData.GENERATE_IMAGE:
            yield "Генерирую изображение бункера..."
            try:
                self.image_prompt = await self.ai_client.generate_message([
                {"role": "system", "content": "You are Stable Diffusion prompt generator. Always respond in English"},
                {"role": "user", "content": f"""Generate a Stable Diffusion prompt for following disaster: {self.disaster_info}
Describe the nature that is around the bunker, without mentioning the bunker in the prompt.
Answer only with prompt, without any other text.
Generate "tags" for the prompt, like "dark, atmospheric, disaster, etc."
The image should be dark, atmospheric, and show the interior of the bunker with all the mentioned items visible."""}])

                self.image = await self.ai_client.generate_image(self.image_prompt)
            except Exception as e:
                print(f"Ошибка при генерации изображения бункера: {e}")
                self.image = None
        
    def get_description(self) -> str:
        """
        Получение форматированного описания бункера
        
        Returns:
            str: Форматированное описание бункера
        """
        items_str = ", ".join(self.items)

        return (
            "**Информация о бедствии:**\n"
            f"{self.disaster_info}\n\n"
            "**Описание бункера:**\n"
            f"{self.bunker_info}\n\n"
            f"> **Размер бункера**: {self.size}\n"
            f"> **Время нахождения**: {self.duration}\n"
            f"> **Количество еды**: {self.food}\n"
            f"> **В бункере имеется**: {items_str}\n\n"
            "В зависимости от того, что находится в бункере, вам предстоит определить, "
            "кто из выживших будет более полезен, учитывая данные обстоятельства."
        )
        
    def get_image_file(self) -> Optional[discord.File]:
        """
        Конвертирует PIL Image в файл Discord для отправки
        
        Returns:
            Optional[discord.File]: Файл изображения или None, если изображение отсутствует
        """
        if self.image is None:
            return None
            
        image_bytes = BytesIO()
        self.image.save(image_bytes, format='PNG')
        image_bytes.seek(0)
        return discord.File(image_bytes, filename='bunker.png')


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
    def generate_status_image(players: List[Player]) -> BytesIO:
        """
        Генерация изображения с таблицей статусов игроков
        
        Args:
            players: Список игроков
            
        Returns:
            BytesIO: Файл с изображением таблицы статусов
        """
        try:
            # Используем всех игроков вместо только активных
            all_players = players
            
            # Определяем шрифты и цвета в стиле Material Design
            font_path = os.path.join(os.path.dirname(__file__), 'fonts/arial.ttf')
            if not os.path.exists(font_path):
                possible_paths = [
                    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
                    "/usr/share/fonts/TTF/Arial.ttf",
                    "C:/Windows/Fonts/arial.ttf",
                    "/System/Library/Fonts/Arial.ttf"
                ]
                
                for path in possible_paths:
                    if os.path.exists(path):
                        font_path = path
                        break
                else:
                    header_font = ImageFont.load_default()
                    cell_font = ImageFont.load_default()
                    font_path = "default"
            
            if font_path != "default":
                try:
                    header_font = ImageFont.truetype(font_path, 18)  # Увеличили размер шрифта заголовка
                    cell_font = ImageFont.truetype(font_path, 14)   # Увеличили размер шрифта ячеек
                except:
                    header_font = ImageFont.load_default()
                    cell_font = ImageFont.load_default()
            
            # Material Design цвета
            colors = {
                'background': (250, 250, 250),      # Светло-серый фон
                'header_bg': (33, 150, 243),        # Material Blue
                'header_text': (255, 255, 255),     # Белый текст заголовка
                'row_even': (255, 255, 255),        # Белый для четных строк
                'row_odd': (245, 245, 245),         # Светло-серый для нечетных строк
                'text': (33, 33, 33),               # Темно-серый текст
                'inactive_text': (158, 158, 158),   # Серый для неактивных игроков
                'border': (224, 224, 224),          # Светло-серая граница
                'shadow': (0, 0, 0, 30)             # Тень для заголовка
            }
            
            # Определяем колонки
            columns = ["Игрок", "Пол", "Тело", "Черта", "Проф.", "Здоровье", "Хобби", "Фобия", "Инв.", "Рюкзак", "Доп."]
            
            # Определяем максимальные ширины для каждой колонки
            max_column_widths = [200, 150, 150, 150, 150, 150, 150, 150, 150, 200, 200]
            
            # Рассчитываем минимальные ширины колонок на основе заголовков
            min_column_widths = []
            for column in columns:
                if hasattr(header_font, 'getbbox'):
                    width = header_font.getbbox(column)[2]
                else:
                    width = header_font.getsize(column)[0]
                min_column_widths.append(width + 30)  # Увеличили отступ
            
            # Подготавливаем данные игроков и рассчитываем необходимую ширину для каждой колонки
            player_data_rows = []
            column_widths = min_column_widths.copy()
            
            for i, player in enumerate(all_players):
                player_data = [
                    f"[{i+1}] {player.name}",
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
                player_data_rows.append((player_data, player.is_active))
                
                for i, data in enumerate(player_data):
                    if hasattr(cell_font, 'getbbox'):
                        width = cell_font.getbbox(data)[2]
                    else:
                        width = cell_font.getsize(data)[0]
                    column_widths[i] = min(max(column_widths[i], width + 30), max_column_widths[i])
            
            # Рассчитываем размеры изображения
            padding = 20  # Увеличили отступы
            header_height = 50  # Увеличили высоту заголовка
            min_cell_height = 40  # Увеличили минимальную высоту ячейки
            
            # Рассчитываем высоту для каждого ряда
            row_heights = []
            
            for player_data, is_active in player_data_rows:
                max_height = min_cell_height
                for i, data in enumerate(player_data):
                    lines, height = ImageGenerator.wrap_text(data, column_widths[i] - 20, cell_font)
                    max_height = max(max_height, height + 15)  # Увеличили отступ
                row_heights.append(max_height)
            
            # Общая ширина и высота изображения
            width = sum(column_widths) + padding * 2
            height = header_height + sum(row_heights) + padding * 2
            
            # Создаем изображение
            image = Image.new('RGB', (width, height), color=colors['background'])
            draw = ImageDraw.Draw(image)
            
            # Рисуем заголовок с тенью
            x = padding
            y = padding
            
            # Рисуем тень заголовка
            shadow_rect = (x, y + 2, x + sum(column_widths), y + header_height + 2)
            draw.rectangle(shadow_rect, fill=colors['shadow'])
            
            # Рисуем сам заголовок
            header_rect = (x, y, x + sum(column_widths), y + header_height)
            draw.rectangle(header_rect, fill=colors['header_bg'])
            
            # Рисуем текст заголовка
            x = padding
            for i, column in enumerate(columns):
                if hasattr(header_font, 'getbbox'):
                    text_width = header_font.getbbox(column)[2]
                    text_height = header_font.getbbox(column)[3]
                else:
                    text_width, text_height = header_font.getsize(column)
                
                text_x = x + (column_widths[i] - text_width) / 2
                text_y = y + (header_height - text_height) / 2
                
                draw.text((text_x, text_y), column, font=header_font, fill=colors['header_text'])
                x += column_widths[i]
            
            # Рисуем данные игроков
            current_y = padding + header_height
            
            for row, ((player_data, is_active), row_height) in enumerate(zip(player_data_rows, row_heights)):
                x = padding
                
                for i, data in enumerate(player_data):
                    # Выбираем цвет фона в зависимости от четности строки
                    cell_color = colors['row_even'] if row % 2 == 0 else colors['row_odd']
                    
                    # Рисуем ячейку с закругленными углами
                    cell_rect = (x, current_y, x + column_widths[i], current_y + row_height)
                    draw.rectangle(cell_rect, fill=cell_color, outline=colors['border'])
                    
                    # Делаем перенос текста и отрисовываем его
                    lines, _ = ImageGenerator.wrap_text(data, column_widths[i] - 20, cell_font)
                    line_height = (cell_font.getbbox('A')[3] if hasattr(cell_font, 'getbbox') else cell_font.getsize('A')[1]) + 4
                    
                    # Рассчитываем вертикальный отступ
                    total_text_height = len(lines) * line_height
                    y_offset = (row_height - total_text_height) / 2
                    
                    # Выбираем цвет текста в зависимости от активности игрока
                    text_color = colors['inactive_text'] if not is_active else colors['text']
                    
                    for j, line in enumerate(lines):
                        line_y = current_y + y_offset + j * line_height
                        draw.text((x + 10, line_y), line, font=cell_font, fill=text_color)
                    
                    x += column_widths[i]
                
                current_y += row_height
            
            # Сохраняем изображение в байты
            image_bytes = BytesIO()
            image.save(image_bytes, format='PNG')
            image_bytes.seek(0)

            return image_bytes
            
            # return discord.File(image_bytes, filename='status.png')
        
        except Exception as e:
            print(f"Ошибка при создании изображения: {e}")
            # Создаем простое изображение с сообщением об ошибке
            error_image = Image.new('RGB', (400, 100), color=colors['background'])
            draw = ImageDraw.Draw(error_image)
            
            try:
                font = ImageFont.load_default()
                draw.text((10, 10), f"Ошибка создания изображения: {str(e)[:50]}", font=font, fill=(255, 0, 0))
            except:
                draw.text((10, 10), "Ошибка создания изображения", fill=(255, 0, 0))
            
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
    
    async def generate_bunker(self):
        """Генерация бункера"""

        async for status_msg in self.bunker.generate():
            logging.info(status_msg)
            yield status_msg
    
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

    async def end_game(self, bot, winner=None, reason="") -> None:
        """
        Единый метод для завершения игры
        
        Args:
            bot: Объект бота Discord
            winner: Опциональный объект игрока-победителя
            reason: Причина завершения игры
        """
        try:
            # Импортируем локально для избежания циклического импорта
            logger = logging.getLogger('bunker_game')
            
            # Изменение статуса игры
            self.status = "finished"
            
            # Получение канала
            channel = bot.get_channel(self.channel_id)
            if not channel:
                logger.error(f"Ошибка: канал {self.channel_id} не найден при завершении игры")
                return
            
            # Открываем все атрибуты у всех игроков
            for player in self.players:
                for attribute in ["gender", "body", "trait", "profession", "health", 
                                "hobby", "phobia", "inventory", "backpack", "additional"]:
                    player.reveal_attribute(attribute)
            
            # Отправляем финальную таблицу в общий чат
            status_image_bytes = self.generate_status_image()
            status_image = discord.File(status_image_bytes, filename='status.png')
            await channel.send("📊 Финальная таблица всех игроков:", file=status_image)
            
            # Если есть победитель, отправляем уведомление о победе
            if winner:
                winner_embed = discord.Embed(
                    title="🏆 Игра завершена!",
                    description=f"**{winner.name}** - единственный выживший в бункере! Поздравляем с победой!",
                    color=discord.Color.gold()
                )
                await channel.send(embed=winner_embed)
                
                # Отправляем уведомление о победе победителю в ЛС
                try:
                    winner_user = bot.get_user(winner.id)
                    if winner_user:
                        dm_channel = await winner_user.create_dm()
                        winner_dm_embed = discord.Embed(
                            title="🏆 Поздравляем с победой!",
                            description="Вы стали единственным выжившим в бункере!",
                            color=discord.Color.gold()
                        )
                        await dm_channel.send(embed=winner_dm_embed)
                except Exception as e:
                    logger.error(f"Ошибка при отправке уведомления победителю: {e}")
            else:
                # Если нет конкретного победителя, просто объявляем о завершении
                active_players = self.get_active_players()
                player_names = ", ".join([p.name for p in active_players])
                
                end_embed = discord.Embed(
                    title="🏁 Игра завершена!",
                    description=f"Игра 'Бункер' завершена. Выжившие в бункере: {player_names}",
                    color=discord.Color.blue()
                )
                
                if reason:
                    end_embed.description += f"\n\nПричина завершения: {reason}"
                
                await channel.send(embed=end_embed)
            
            # Удаляем игру из словаря активных игр
            # Используем функцию globals() для доступа к глобальной переменной из импортирующего модуля
            # Это будет работать, только если переменная active_games доступна в глобальном пространстве имен
            try:
                import sys
                main_module = sys.modules.get('__main__')
                if hasattr(main_module, 'active_games') and self.channel_id in main_module.active_games:
                    del main_module.active_games[self.channel_id]
                    logger.info(f"Игра удалена из списка активных игр в канале {self.channel_id}")
            except Exception as e:
                logger.error(f"Не удалось удалить игру из списка активных: {e}")
            
            logger.info(f"Игра в канале {self.channel_id} завершена" + (f": {reason}" if reason else ""))
            
            # Запускаем анализ выживания в бункере с оставшимися игроками
            if self.get_active_players():
                # await channel.send("🧠 А теперь посмотрим, как нейросеть оценивает шансы этой группы на выживание...")
                await self.analyze_bunker_survival(bot)
        except Exception as e:
            logger.error(f"Ошибка при завершении игры: {e}")

    async def analyze_bunker_survival(self, bot) -> None:
        """
        Анализ с помощью нейросети шансов выживания бункера с текущим составом игроков
        
        Args:
            bot: Объект бота Discord для отправки сообщений
        """
        try:
            # Получаем канал
            channel = bot.get_channel(self.channel_id)
            if not channel:
                return
            
            # Получаем только активных игроков
            active_players = self.get_active_players()
            if not active_players:
                await channel.send("Некому выживать в бункере!")
                return
            
            # Уведомление о начале анализа
            analyzing_message = await channel.send("🔍 Анализирую шансы выживания обитателей бункера...")
            
            # Формируем полную информацию о бункере
            bunker_info = self.bunker.get_description()
            
            # Формируем информацию о выживших (используем полные данные)
            survivors_info = []
            for i, player in enumerate(active_players, 1):
                # Используем полную информацию о персонаже
                player_card = player.get_character_card()
                survivors_info.append(f"**Игрок {i}: {player.name}**\n{player_card}")
            
            survivors_text = "\n\n".join(survivors_info)
            
            # Формируем общий промпт для нейросети
            prompt = f"""Проанализируй шансы на выживание группы людей в бункере при данных условиях.
            
ИНФОРМАЦИЯ О КАТАСТРОФЕ И БУНКЕРЕ:
{bunker_info}

ИНФОРМАЦИЯ О ВЫЖИВШИХ В БУНКЕРЕ ({len(active_players)} человек):
{survivors_text}

Оцени по следующим критериям:
1. Какие конфликты могут возникнуть между обитателями бункера
2. Сильные и слабые стороны группы и предметов
3. Посчитай вероятность выживания группы в процентах
"""
            
            # Отправляем запрос нейросети
            survival_analysis = await self.ai_client.generate_message([
                {"role": "system", "content": "Ты эксперт по выживанию. Анализируешь шансы выжить группе людей в бункере в условиях постапокалипсиса. Отвечай подробно, учитывай совместимость профессий, навыков и особенностей людей."},
                {"role": "user", "content": prompt}
            ])
            
            # Удаляем сообщение о процессе анализа
            try:
                await analyzing_message.delete()
            except:
                pass
            
            # Отправляем результат, разбивая на части при необходимости
            await self._send_analysis_results(channel, survival_analysis)
        except Exception as e:
            import logging
            logger = logging.getLogger('bunker_game')
            logger.error(f"Ошибка при анализе выживания бункера: {e}")
            try:
                await channel.send(f"Произошла ошибка при анализе выживания: {e}")
            except:
                pass
    
    async def _send_analysis_results(self, channel, analysis_text):
        """
        Отправляет результаты анализа в канал, разбивая на несколько сообщений при необходимости
        
        Args:
            channel: Канал Discord для отправки
            analysis_text: Текст анализа от нейросети
        """
        # Максимальная длина текста в одном embed
        MAX_EMBED_LENGTH = 1000
        
        # Заголовок для embed
        title = "🔍 Анализ выживания в бункере"
        
        # Разбиваем текст на части, если он слишком длинный
        if len(analysis_text) <= MAX_EMBED_LENGTH:
            # Если текст короткий, отправляем одним сообщением
            embed = discord.Embed(
                title=title,
                description=analysis_text,
                color=discord.Color.blue()
            )
            await channel.send(embed=embed)
        else:
            # Разбиваем текст на равномерные части, стараясь не разрывать предложения
            parts = []
            
            # Сначала делим текст на предложения, чтобы не разрывать их
            # Примитивное разделение по точкам, восклицательным и вопросительным знакам
            sentences = re.split(r'(?<=[.!?]) +', analysis_text)
            
            current_part = ""
            
            for sentence in sentences:
                # Если предложение само по себе длиннее MAX_EMBED_LENGTH, его придется разбить
                if len(sentence) > MAX_EMBED_LENGTH:
                    # Если в текущей части уже что-то есть, сохраняем её
                    if current_part:
                        parts.append(current_part)
                        current_part = ""
                    
                    # Разбиваем длинное предложение по словам
                    words = sentence.split()
                    temp_part = ""
                    
                    for word in words:
                        if len(temp_part) + len(word) + 1 <= MAX_EMBED_LENGTH:
                            temp_part += (word + " ")
                        else:
                            parts.append(temp_part.strip())
                            temp_part = word + " "
                    
                    if temp_part:
                        current_part = temp_part.strip()
                else:
                    # Если добавление предложения превысит лимит, начинаем новую часть
                    if len(current_part) + len(sentence) + 1 > MAX_EMBED_LENGTH:
                        parts.append(current_part)
                        current_part = sentence
                    else:
                        if current_part:
                            current_part += " " + sentence
                        else:
                            current_part = sentence
            
            # Добавляем последнюю часть
            if current_part:
                parts.append(current_part)
            
            # Отправляем каждую часть как отдельный embed
            for i, part in enumerate(parts):
                part_title = f"{title} (Часть {i+1}/{len(parts)})"
                embed = discord.Embed(
                    title=part_title,
                    description=part,
                    color=discord.Color.blue()
                )
                await channel.send(embed=embed) 