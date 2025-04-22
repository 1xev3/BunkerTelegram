from io import BytesIO
import random
from typing import Optional
import discord

from lib.ai_client import G4FClient
from lib.bunker.game_config import GameConfig

from textwrap import dedent


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
        self.theme = random.choice(GameConfig.BUNKER_THEMES)
        self.size = random.choice(GameConfig.BUNKER_SIZES)
        self.duration = random.choice(GameConfig.BUNKER_DURATIONS)
        self.food = random.choice(GameConfig.FOOD_SUPPLIES)
        # Выбираем от 2 до 5 случайных предметов
        self.items = random.sample(GameConfig.BUNKER_ITEMS, k=random.randint(1, GameConfig.BUNKER_ITEMS_COUNT_MAX))
        items_str = ", ".join(self.items)

        self.disaster_info = f"Тема: {self.theme}"
        if GameConfig.GENERATE_DISASTER:  
            yield "Генерирую катаклизм..."
            self.disaster_info = await self.ai_client.generate_message([
                {"role": "system", "content": "You are a helpful assistant that generates bunker disaster descriptions for a bunker game. Always respond in User language."},
                {"role": "user", "content": dedent(f"""Сгенерируй случайный смертельный катаклизм для игры в\
                    бункер на тему: {self.theme}. 
                    Катаклизм - это то что происходит за пределами бункера! Не упоминай бункер в описании катаклизма.
                    В зависимости от этого игроки будут выбирать кто заслуживает место в бункере. 
                    В ответе оставь только само описание, не пиши ничего от своего имени. 
                    В ответе укажи название катаклизма, его описание и с чём предстоит столкнуться вне бункера.
                """)}])
        
        self.bunker_info = ""
        if GameConfig.GENERATE_BUNKER_DESC:
            yield "Генерирую описание бункера..."
            self.bunker_info = await self.ai_client.generate_message([
                {"role": "system", "content": "You are description generator for a bunker game. Always respond in User language."},
                {"role": "user", "content": dedent(f"""Сгенерируй краткое описание бункера по его характеристикам. Придумай какие комнаты в нём есть (в зависимости от размера и предметов в нём).
                    В ответе оставь только само описание, не пиши ничего от своего имени. 
                    Вот характеристики бункера: 
                    Размер: {self.size}
                    Еда: {self.food}
                    Предметы: {items_str}
                """)}])

        # Генерация изображения бункера
        if GameConfig.GENERATE_IMAGE:
            yield "Генерирую изображение бункера..."
            try:
                self.image_prompt = await self.ai_client.generate_message([
                {"role": "system", "content": "You are Stable Diffusion prompt generator. Always respond in English"},
                {"role": "user", "content": dedent(f"""Generate a Stable Diffusion prompt for following disaster: {self.disaster_info}
                    Describe the nature that is around the bunker, without mentioning the bunker in the prompt.
                    Answer only with prompt, without any other text.
                    Generate "tags" for the prompt, like "dark, atmospheric, disaster, etc."
                    The image should be dark, atmospheric, and show the interior of the bunker with all the mentioned items visible.
                """)}])

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