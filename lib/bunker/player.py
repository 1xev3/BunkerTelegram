

import random
from typing import Any, List, Optional, Tuple
from textwrap import dedent

import numpy as np

from lib.ai_client import G4FClient
from lib.bunker.game_config import GameConfig

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
        gender = weighed_random(GameConfig.GENDERS)
        gender_affix = weighed_random(GameConfig.GENDER_AFFIXES)
        years_old = weighed_random(GameConfig.AGES)
        years_old = random.randint(years_old[0], years_old[1])
        self.gender = f"{gender} {gender_affix} ({years_old} лет)"

        # Генерация телосложения
        body = weighed_random(GameConfig.BODY_TYPES)
        
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
        self.trait = random.choice(GameConfig.TRAITS)
        
        # Генерация профессии с уровнем
        profession = random.choice(GameConfig.PROFESSIONS)
        profession_level = weighed_random(GameConfig.SKILL_LEVELS)
        self.profession = f"{profession} ({profession_level})"
        
        # Генерация здоровья
        health = weighed_random(GameConfig.HEALTH_STATES)
        health_stage = weighed_random(GameConfig.HEALTH_STAGES)
        if health != "Здоров":
            self.health = f"{health} ({health_stage})"
        else:
            self.health = health
        
        # Генерация хобби с уровнем
        hobby = random.choice(GameConfig.HOBBIES)
        hobby_level = weighed_random(GameConfig.SKILL_LEVELS)
        self.hobby = f"{hobby} ({hobby_level})"
        
        self.phobia = random.choice(GameConfig.PHOBIAS)
        self.inventory = random.choice(GameConfig.INVENTORY)
        
        # Генерация от 1 до 3 предметов для рюкзака
        backpack_items_count = random.randint(1, GameConfig.BACKPACK_ITEMS_COUNT_MAX)
        backpack_items = random.sample(GameConfig.BACKPACK_ITEMS, k=backpack_items_count)
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
        
        self.additional = random.choice(GameConfig.ADDITIONAL_INFO)

        self.description = ""
        if GameConfig.GENERATE_CHARACTER_DESC:
            self.description = await ai_client.generate_message([
                {"role": "system", "content": "You are a helpful assistant that generates character descriptions for a bunker game. Always respond in User language."},
                {"role": "user", "content": dedent(f"""Сгенерируй краткое внешнее описание для персонажа. 
                    В ответе оставь только само описание, не пиши ничего от своего имени.
                    Придумай для персонажа: Имя, цвет глаз, цвет волос, стиль причёски, цвет кожи, стиль одежды, цвета одежды
                    Вот досье персонажа, которого нужно сгенерировать (исходя из него, придумывай): {self.get_character_card()}
                """)}])
                
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
            return getattr(self, attribute, "err") #attribute_map.get(attribute)
        return None