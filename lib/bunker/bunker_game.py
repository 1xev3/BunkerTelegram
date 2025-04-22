import discord
from typing import List, Dict, Optional
import logging
import re

from lib.ai_client import G4FClient
from lib.bunker.player import Player
from lib.bunker.bunker import Bunker
from lib.bunker.image_generator import ImageGenerator



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