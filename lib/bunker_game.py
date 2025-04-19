import random
import discord
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
from io import BytesIO

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

        # Генерация пола
        gender = random.choice(GameData.GENDERS)
        years_old = random.randint(12, 95)
        self.gender = f"{gender} ({years_old} лет)"

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
        if random.random() < GameData.SPECIAL_ABILITIES_CHANCE:
            self.special_ability = random.choice(GameData.SPECIAL_ABILITIES)
        else:
            self.special_ability = ""

        self.description = ""
        self.description = await ai_client.generate_message([
            {"role": "system", "content": "You are a helpful assistant that generates character descriptions for a bunker game. Always respond in User language."},
            {"role": "user", "content": f"""Сгенерируй краткую биографию для персонажа. 
В ответе оставь только само описание, не пиши ничего от своего имени.
В биографию так-же включи: Имя, цвет глаз, цвет волос, цвет кожи (их тоже сделай случайными). 
Сгенерируй биографию от лица персонажа. Сгенерируй всё одним предложением. 
Вот досье персонажа, которого нужно сгенерировать: {self.get_character_card()}"""}])
    
    def get_character_card(self) -> str:
        """
        Получение форматированной карточки персонажа
        
        Returns:
            str: Форматированное описание персонажа
        """
        return (
            f"{self.description}\n"
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
        self.image_url = None
    
    async def generate(self) -> None:
        """Генерация случайного бункера"""
        self.size = random.choice(GameData.BUNKER_SIZES)
        self.duration = random.choice(GameData.BUNKER_DURATIONS)
        self.food = random.choice(GameData.FOOD_SUPPLIES)
        # Выбираем от 2 до 5 случайных предметов
        self.items = random.sample(GameData.BUNKER_ITEMS, k=random.randint(1, 5))

        self.disaster_info = await self.ai_client.generate_message([
            {"role": "system", "content": "You are a helpful assistant that generates bunker disaster descriptions for a bunker game. Always respond in User language."},
            {"role": "user", "content": f"""Сгенерируй случайный смертельный катаклизм для игры в\
бункер на тему: {random.choice(GameData.BUNKER_THEMES)}. 
Катаклизм - это то что происходит за пределами бункера! 
В зависимости от этого игроки будут выбирать кто заслуживает место в бункере. 
В ответе оставь только само описание, не пиши ничего от своего имени. 
В ответе укажи название катаклизма, его описание и последствия."""}])

        # Генерация изображения бункера
        try:
            self.image_prompt = await self.ai_client.generate_message([
                {"role": "system", "content": "You are Stable Diffusion prompt generator. Always respond in English"},
                {"role": "user", "content": f"""Generate a Stable Diffusion prompt for following disaster: {self.disaster_info}
Describe the nature that is around the bunker, without mentioning the bunker in the prompt.
Answer only with prompt, without any other text.
Generate "tags" for the prompt, like "dark, atmospheric, disaster, etc."
The image should be dark, atmospheric, and show the interior of the bunker with all the mentioned items visible."""}])

            self.image_url = await self.ai_client.generate_image(self.image_prompt)
        except Exception as e:
            print(f"Ошибка при генерации изображения бункера: {e}")
            self.image_url = None
    
    def get_description(self) -> str:
        """
        Получение форматированного описания бункера
        
        Returns:
            str: Форматированное описание бункера
        """
        items_str = ", ".join(self.items)

        return (
            "**Описание найденного бункера**\n\n"
            f"{self.disaster_info}\n\n"
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
    
    async def generate_bunker(self) -> None:
        """Генерация бункера"""
        await self.bunker.generate()
    
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