import discord
from discord.ext import commands
import asyncio
import random
import os
import logging
from typing import Dict, List, Optional, Union, Callable, Any
from dotenv import load_dotenv
from discord import app_commands
from bunker_game import BunkerGame, Player, Bunker, ImageGenerator
from logging_config import setup_logging

# Настройка логирования
logger = setup_logging()

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Настройка интентов
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True

# Инициализация бота
bot = commands.Bot(command_prefix='/', intents=intents)
active_games: Dict[int, BunkerGame] = {}  # Словарь для хранения активных игр

@bot.event
async def on_ready():
    """Обработчик события готовности бота"""
    logger.info(f'Бот {bot.user} запущен и готов к работе!')
    try:
        synced = await bot.tree.sync()
        logger.info(f"Синхронизировано {len(synced)} команд")
    except Exception as e:
        logger.error(f"Ошибка синхронизации команд: {e}", exc_info=True)

# Глобальный обработчик ошибок
@bot.event
async def on_error(event, *args, **kwargs):
    """Глобальный обработчик ошибок событий"""
    logger.error(f"Произошла ошибка в событии {event}:", exc_info=True)

@bot.event
async def on_command_error(ctx, error):
    """Обработчик ошибок команд бота"""
    logger.error(f"Ошибка команды: {error}", exc_info=True)
    if isinstance(error, commands.CommandNotFound):
        return
    await ctx.send(f"Произошла ошибка: {error}")

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    """Обработчик ошибок слеш-команд"""
    logger.error(f"Ошибка слеш-команды: {error}", exc_info=True)
    if not interaction.response.is_done():
        await interaction.response.send_message(f"Произошла ошибка: {error}", ephemeral=True)
    else:
        await interaction.followup.send(f"Произошла ошибка: {error}", ephemeral=True)

@bot.tree.command(name="start", description="Начать новую игру Бункер")
async def start_game(interaction: discord.Interaction):
    """Команда для начала новой игры Бункер"""
    channel = interaction.channel
    
    # Проверка на существование активной игры в этом канале
    if channel.id in active_games:
        await interaction.response.send_message("В этом канале уже идет игра. Дождитесь её окончания или используйте другой канал.", ephemeral=True)
        return
    
    # Создание новой игры
    game = BunkerGame(interaction.user.id, channel.id)
    active_games[channel.id] = game
    
    # Создание эмбеда для приглашения игроков
    embed = discord.Embed(
        title="🚨 Игра Бункер началась! 🚨",
        description="Нажмите кнопку ниже, чтобы присоединиться к игре.\n\nУчастники:",
        color=discord.Color.red()
    )
    
    # Добавление создателя игры как первого участника
    player = Player(interaction.user.id, interaction.user.name)
    game.add_player(player)
    embed.description += f"\n1. {interaction.user.name}"
    
    # Создание кнопки для присоединения
    view = JoinGameView(game)
    
    await interaction.response.send_message(embed=embed, view=view)
    message = await interaction.original_response()
    game.message_id = message.id
    
    # Отправка управления администратору
    await send_admin_controls(interaction.user, game)
    
    logger.info(f"Создана новая игра в канале {channel.id} пользователем {interaction.user.name}")

# Класс для кнопки присоединения к игре
class JoinGameView(discord.ui.View):
    """Класс представления с кнопкой для присоединения к игре"""
    
    def __init__(self, game: BunkerGame):
        """
        Инициализация представления
        
        Args:
            game: Игра, к которой будут присоединяться игроки
        """
        super().__init__(timeout=None)
        self.game = game
    
    @discord.ui.button(label="Присоединиться", style=discord.ButtonStyle.green, custom_id="join_game")
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Обработчик нажатия на кнопку присоединения"""
        try:
            # Проверка на максимальное количество игроков
            if len(self.game.players) >= 15:
                await interaction.response.send_message("Игра уже заполнена! Максимум 15 игроков.", ephemeral=True)
                return
            
            # Проверка, не присоединился ли уже игрок
            if any(player.id == interaction.user.id for player in self.game.players):
                await interaction.response.send_message("Вы уже присоединились к игре!", ephemeral=True)
                return
            
            # Добавление нового игрока
            player = Player(interaction.user.id, interaction.user.name)
            self.game.add_player(player)
            
            # Обновление эмбеда со списком игроков
            await self._update_player_list(interaction)
            
            await interaction.response.send_message(f"Вы присоединились к игре Бункер!", ephemeral=True)
            logger.info(f"Игрок {interaction.user.name} присоединился к игре в канале {interaction.channel.id}")
        except Exception as e:
            logger.error(f"Ошибка при присоединении к игре: {e}", exc_info=True)
            if not interaction.response.is_done():
                await interaction.response.send_message("Произошла ошибка при присоединении к игре. Попробуйте еще раз.", ephemeral=True)
    
    async def _update_player_list(self, interaction: discord.Interaction) -> None:
        """
        Обновляет список игроков в сообщении
        
        Args:
            interaction: Объект взаимодействия Discord
        """
        try:
            channel = interaction.channel
            message = await channel.fetch_message(self.game.message_id)
            embed = message.embeds[0]
            
            # Обновление списка игроков
            player_list = "\n".join([f"{i+1}. {player.name}" for i, player in enumerate(self.game.players)])
            embed.description = f"Нажмите кнопку ниже, чтобы присоединиться к игре.\n\nУчастники:\n{player_list}"
            
            await message.edit(embed=embed)
        except Exception as e:
            logger.error(f"Ошибка при обновлении списка игроков: {e}", exc_info=True)

# Отправка элементов управления администратору
async def send_admin_controls(admin: discord.User, game: BunkerGame) -> None:
    """
    Отправляет панель управления игрой администратору
    
    Args:
        admin: Объект пользователя-администратора
        game: Объект игры
    """
    try:
        dm_channel = await admin.create_dm()
        embed = discord.Embed(
            title="Управление игрой Бункер",
            description="Используйте кнопки ниже для управления игрой",
            color=discord.Color.blue()
        )
        view = AdminControlView(game)
        message = await dm_channel.send(embed=embed, view=view)
        game.admin_message_id = message.id
        logger.info(f"Отправлены элементы управления администратору {admin.name}")
    except Exception as e:
        logger.error(f"Ошибка при отправке управления администратору {admin.name}: {e}", exc_info=True)

# Класс для кнопок управления администратора
class AdminControlView(discord.ui.View):
    """Класс представления с кнопками для управления игрой администратором"""
    
    def __init__(self, game: BunkerGame):
        """
        Инициализация представления
        
        Args:
            game: Объект игры для управления
        """
        super().__init__(timeout=None)
        self.game = game
    
    @discord.ui.button(label="Начать игру", style=discord.ButtonStyle.green, custom_id="start_game")
    async def start_game_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Обработчик нажатия кнопки начала игры"""
        try:
            # Отложенный ответ, чтобы избежать ошибки истечения взаимодействия
            await interaction.response.defer(ephemeral=True)
            
            # Проверка, достаточно ли игроков
            if len(self.game.players) < 1:#if len(self.game.players) < 2:
                await interaction.followup.send("Для начала игры нужно минимум 2 игрока!", ephemeral=True)
                return
            
            # Изменение состояния игры
            self.game.status = "running"
            
            # Генерация бункера и персонажей
            self.game.generate_bunker()
            self.game.generate_player_cards()
            
            # Уведомление в канале
            channel = bot.get_channel(self.game.channel_id)
            await channel.send("Игра началась! Всем игрокам отправлена информация в личных сообщениях.")
            
            # Отправка информации игрокам
            await self.send_game_info_to_players()
            
            # Обновление контроллов администратора
            await self._update_admin_controls(interaction)
            
            await interaction.followup.send("Игра успешно запущена!", ephemeral=True)
            logger.info(f"Игра запущена в канале {self.game.channel_id}")
        except Exception as e:
            logger.error(f"Ошибка при запуске игры: {e}", exc_info=True)
            await interaction.followup.send(f"Произошла ошибка при запуске игры: {e}", ephemeral=True)
    
    @discord.ui.button(label="Следующий раунд", style=discord.ButtonStyle.primary, custom_id="next_round", row=1)
    async def next_round_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Обработчик нажатия кнопки следующего раунда"""
        try:
            # Отложенный ответ
            await interaction.response.defer(ephemeral=True)
            
            # Проверка, запущена ли игра
            if self.game.status != "running":
                await interaction.followup.send("Игра еще не запущена или уже завершена!", ephemeral=True)
                return
            
            # Переход к следующему раунду
            round_num = self.game.next_round()
            
            # Уведомление в канале
            channel = bot.get_channel(self.game.channel_id)
            await channel.send(f"Начинается раунд {round_num}! Обсудите, кого следует исключить из бункера.")
            
            await interaction.followup.send(f"Вы начали раунд {round_num}.", ephemeral=True)
            logger.info(f"Начат раунд {round_num} в игре в канале {self.game.channel_id}")
        except Exception as e:
            logger.error(f"Ошибка при переходе к следующему раунду: {e}", exc_info=True)
            await interaction.followup.send(f"Произошла ошибка: {e}", ephemeral=True)
    
    @discord.ui.button(label="Изгнать участника", style=discord.ButtonStyle.danger, custom_id="exile_player", row=1)
    async def exile_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Обработчик нажатия кнопки изгнания участника"""
        try:
            # Отложенный ответ
            await interaction.response.defer(ephemeral=True)
            
            # Проверка, запущена ли игра
            if self.game.status != "running":
                await interaction.followup.send("Игра еще не запущена или уже завершена!", ephemeral=True)
                return
            
            # Проверка, есть ли активные игроки
            active_players = self.game.get_active_players()
            if len(active_players) <= 2:
                await interaction.followup.send("Осталось слишком мало игроков для голосования!", ephemeral=True)
                return
            
            # Создание меню для выбора игрока
            options = [
                discord.SelectOption(
                    label=player.name,
                    value=str(player.id),
                    description=f"Игрок {player.name}"
                ) for player in active_players
            ]
            
            # Отправка меню выбора
            view = ExileSelectView(self.game)
            view.add_item(ExileSelect(options, self.game))
            
            await interaction.followup.send("Выберите игрока для изгнания:", view=view, ephemeral=True)
        except Exception as e:
            logger.error(f"Ошибка при выборе игрока для изгнания: {e}", exc_info=True)
            await interaction.followup.send(f"Произошла ошибка: {e}", ephemeral=True)
    
    @discord.ui.button(label="Закончить игру", style=discord.ButtonStyle.secondary, custom_id="end_game", row=1)
    async def end_game_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Обработчик нажатия кнопки завершения игры"""
        try:
            # Отложенный ответ
            await interaction.response.defer(ephemeral=True)
            
            # Завершение игры
            self.game.status = "finished"
            
            # Уведомление в канале
            channel = bot.get_channel(self.game.channel_id)
            
            # Подсчет активных игроков
            active_players = self.game.get_active_players()
            player_names = ", ".join([p.name for p in active_players])
            
            await channel.send(f"Игра завершена! Выжившие в бункере: {player_names}")
            
            # Удаление игры из активных
            if self.game.channel_id in active_games:
                del active_games[self.game.channel_id]
            
            await interaction.followup.send("Вы завершили игру.", ephemeral=True)
            
            # Деактивация кнопок
            for item in self.children:
                item.disabled = True
            
            # Получаем канал и сообщение заново
            try:
                dm_channel = await interaction.user.create_dm()
                message = await dm_channel.fetch_message(self.game.admin_message_id)
                await message.edit(view=self)
            except discord.NotFound:
                logger.warning("Сообщение администратора не найдено")
            
            logger.info(f"Игра в канале {self.game.channel_id} завершена")
        except Exception as e:
            logger.error(f"Ошибка при завершении игры: {e}", exc_info=True)
            await interaction.followup.send(f"Произошла ошибка: {e}", ephemeral=True)
    
    async def _update_admin_controls(self, interaction: discord.Interaction) -> None:
        """
        Обновляет контроллы администратора после начала игры
        
        Args:
            interaction: Объект взаимодействия Discord
        """
        try:
            # Обновляем кнопки
            self.clear_items()
            self.add_item(discord.ui.Button(label="Следующий раунд", style=discord.ButtonStyle.primary, custom_id="next_round"))
            self.add_item(discord.ui.Button(label="Изгнать участника", style=discord.ButtonStyle.danger, custom_id="exile_player"))
            self.add_item(discord.ui.Button(label="Закончить игру", style=discord.ButtonStyle.secondary, custom_id="end_game"))
            
            # Получаем канал и сообщение заново, так как взаимодействие уже отложено
            dm_channel = await interaction.user.create_dm()
            try:
                message = await dm_channel.fetch_message(self.game.admin_message_id)
                await message.edit(view=self)
            except discord.NotFound:
                # Если сообщение не найдено, отправляем новое
                message = await dm_channel.send(embed=discord.Embed(
                    title="Управление игрой Бункер",
                    description="Используйте кнопки ниже для управления игрой",
                    color=discord.Color.blue()
                ), view=self)
                self.game.admin_message_id = message.id
        except Exception as e:
            logger.error(f"Ошибка при обновлении контроллов администратора: {e}", exc_info=True)
    
    async def send_game_info_to_players(self) -> None:
        """Отправка информации о бункере и картах персонажей каждому игроку"""
        for player in self.game.players:
            user = bot.get_user(player.id)
            if user:
                try:
                    # Информация о бункере
                    bunker_embed = discord.Embed(
                        title="🏢 Информация о бункере",
                        description=self.game.bunker.get_description(),
                        color=discord.Color.gold()
                    )
                    
                    # Информация о персонаже
                    player_embed = discord.Embed(
                        title="👤 Ваш персонаж",
                        description=player.get_character_card(),
                        color=discord.Color.green()
                    )
                    
                    # Отправка сообщений
                    dm_channel = await user.create_dm()
                    await dm_channel.send(embed=bunker_embed)
                    
                    # Отправка карточки и кнопок действий
                    view = PlayerActionView(self.game, player)
                    message = await dm_channel.send(embed=player_embed, view=view)
                    player.message_id = message.id
                    
                    # Отправка таблицы с характеристиками всех игроков
                    await self.send_player_status_table(user, player)
                    
                    logger.info(f"Отправлена информация игроку {player.name}")
                except Exception as e:
                    logger.error(f"Ошибка при отправке информации игроку {player.name}: {e}", exc_info=True)
    
    async def send_player_status_table(self, user: discord.User, player: Player) -> None:
        """
        Отправка таблицы статусов игроку
        
        Args:
            user: Объект пользователя Discord
            player: Объект игрока
        """
        # Генерация и отправка изображения
        try:
            status_image = self.game.generate_status_image()
            if status_image:
                dm_channel = await user.create_dm()
                message = await dm_channel.send(
                    content="**📊 Статус игроков**",
                    file=status_image
                )
                player.status_message_id = message.id
                # Удаляем временный файл
                if os.path.exists(status_image.filename):
                    os.remove(status_image.filename)
        except Exception as e:
            logger.error(f"Ошибка при отправке таблицы статусов: {e}", exc_info=True)

# Класс для выбора игрока для изгнания
class ExileSelectView(discord.ui.View):
    """Класс представления с выбором игрока для изгнания"""
    
    def __init__(self, game: BunkerGame):
        """
        Инициализация представления
        
        Args:
            game: Объект игры
        """
        super().__init__(timeout=None)
        self.game = game

# Селект-меню для выбора игрока для изгнания
class ExileSelect(discord.ui.Select):
    """Селект-меню для выбора игрока для изгнания"""
    
    def __init__(self, options: List[discord.SelectOption], game: BunkerGame):
        """
        Инициализация селект-меню
        
        Args:
            options: Список опций для выбора
            game: Объект игры
        """
        super().__init__(
            placeholder="Выберите игрока для голосования на изгнание...",
            min_values=1,
            max_values=1,
            options=options
        )
        self.game = game
    
    async def callback(self, interaction: discord.Interaction):
        """Обработчик выбора игрока для изгнания"""
        try:
            # Отложенный ответ
            await interaction.response.defer(ephemeral=True)
            
            # Получаем выбранного игрока
            target_player = None
            for player in self.game.players:
                if str(player.id) == self.values[0]:
                    target_player = player
                    break
            
            if not target_player:
                await interaction.followup.send("Выбранный игрок не найден!", ephemeral=True)
                return
            
            # Проверяем, активен ли игрок
            if not target_player.is_active:
                await interaction.followup.send("Этот игрок уже исключен из игры!", ephemeral=True)
                return
            
            # Начинаем голосование
            channel = bot.get_channel(self.game.channel_id)
            
            # Создаем эмбед для голосования
            embed = discord.Embed(
                title="🗳️ Голосование за исключение из бункера",
                description=f"Проголосуйте, должен ли **{target_player.name}** быть исключен из бункера.",
                color=discord.Color.orange()
            )
            
            # Сбрасываем голоса перед новым голосованием
            self.game.reset_votes()
            
            # Создаем кнопки для голосования
            vote_view = VoteView(self.game, target_player)
            
            vote_message = await channel.send(embed=embed, view=vote_view)
            
            # Сохраняем ID сообщения с голосованием
            self.game.vote_message_id = vote_message.id
            
            # Запускаем таймер голосования (60 секунд)
            await interaction.followup.send(f"Вы начали голосование за исключение игрока {target_player.name}. Голосование продлится 60 секунд.", ephemeral=True)
            logger.info(f"Начато голосование за исключение игрока {target_player.name} в канале {self.game.channel_id}")
            
            # Ждем 60 секунд
            await asyncio.sleep(60)
            
            # Подсчитываем результаты
            yes_votes = vote_view.yes_votes
            no_votes = vote_view.no_votes
            
            result_embed = discord.Embed(
                title="🗳️ Результаты голосования",
                description=f"Голосование за исключение **{target_player.name}** завершено.\n\n"
                           f"**За исключение**: {yes_votes} голосов\n"
                           f"**Против исключения**: {no_votes} голосов",
                color=discord.Color.blue()
            )
            
            # Определяем результат
            if yes_votes > no_votes:
                result_embed.description += f"\n\n**{target_player.name}** исключен из бункера!"
                # Исключаем игрока
                target_player.is_active = False
                # Обновляем таблицы статусов
                await self.game.update_all_player_tables(bot)
                logger.info(f"Игрок {target_player.name} исключен из игры в канале {self.game.channel_id}")
            else:
                result_embed.description += f"\n\n**{target_player.name}** остается в бункере!"
                logger.info(f"Игрок {target_player.name} остается в игре в канале {self.game.channel_id}")
            
            # Деактивируем кнопки голосования
            for item in vote_view.children:
                item.disabled = True
            
            # Обновляем сообщение с результатами
            await vote_message.edit(embed=result_embed, view=vote_view)
            
            # Проверяем, остался ли только один игрок
            active_players = self.game.get_active_players()
            if len(active_players) == 1:
                winner = active_players[0]
                winner_embed = discord.Embed(
                    title="🏆 Игра завершена!",
                    description=f"**{winner.name}** - единственный выживший в бункере! Поздравляем с победой!",
                    color=discord.Color.gold()
                )
                await channel.send(embed=winner_embed)
                
                # Завершаем игру
                self.game.status = "finished"
                if self.game.channel_id in active_games:
                    del active_games[self.game.channel_id]
                logger.info(f"Игра завершена победой игрока {winner.name} в канале {self.game.channel_id}")
        except Exception as e:
            logger.error(f"Ошибка при голосовании: {e}", exc_info=True)
            await interaction.followup.send(f"Произошла ошибка: {e}", ephemeral=True)

# Класс для кнопок голосования
class VoteView(discord.ui.View):
    """Класс представления с кнопками для голосования"""
    
    def __init__(self, game: BunkerGame, target_player: Player):
        """
        Инициализация представления для голосования
        
        Args:
            game: Объект игры
            target_player: Целевой игрок для голосования
        """
        super().__init__(timeout=None)
        self.game = game
        self.target_player = target_player
        self.yes_votes = 0
        self.no_votes = 0
        self.voted_users = set()  # Множество пользователей, которые уже проголосовали
    
    @discord.ui.button(label="За исключение", style=discord.ButtonStyle.danger, custom_id="vote_yes")
    async def vote_yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Обработчик голоса за исключение"""
        try:
            # Проверяем, участвует ли пользователь в игре
            is_player = any(player.id == interaction.user.id and player.is_active for player in self.game.players)
            if not is_player:
                await interaction.response.send_message("Вы не являетесь активным участником этой игры!", ephemeral=True)
                return
            
            # Проверяем, не голосовал ли пользователь уже
            if interaction.user.id in self.voted_users:
                await interaction.response.send_message("Вы уже проголосовали!", ephemeral=True)
                return
            
            # Учитываем голос
            self.yes_votes += 1
            self.voted_users.add(interaction.user.id)
            
            await interaction.response.send_message("Вы проголосовали за исключение игрока из бункера.", ephemeral=True)
            logger.info(f"Игрок {interaction.user.name} проголосовал ЗА исключение {self.target_player.name}")
        except Exception as e:
            logger.error(f"Ошибка при голосовании за исключение: {e}", exc_info=True)
            if not interaction.response.is_done():
                await interaction.response.send_message(f"Произошла ошибка: {e}", ephemeral=True)
    
    @discord.ui.button(label="Против исключения", style=discord.ButtonStyle.green, custom_id="vote_no")
    async def vote_no(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Обработчик голоса против исключения"""
        try:
            # Проверяем, участвует ли пользователь в игре
            is_player = any(player.id == interaction.user.id and player.is_active for player in self.game.players)
            if not is_player:
                await interaction.response.send_message("Вы не являетесь активным участником этой игры!", ephemeral=True)
                return
            
            # Проверяем, не голосовал ли пользователь уже
            if interaction.user.id in self.voted_users:
                await interaction.response.send_message("Вы уже проголосовали!", ephemeral=True)
                return
            
            # Учитываем голос
            self.no_votes += 1
            self.voted_users.add(interaction.user.id)
            
            await interaction.response.send_message("Вы проголосовали против исключения игрока из бункера.", ephemeral=True)
            logger.info(f"Игрок {interaction.user.name} проголосовал ПРОТИВ исключения {self.target_player.name}")
        except Exception as e:
            logger.error(f"Ошибка при голосовании против исключения: {e}", exc_info=True)
            if not interaction.response.is_done():
                await interaction.response.send_message(f"Произошла ошибка: {e}", ephemeral=True)

# Класс для кнопок действий игрока
class PlayerActionView(discord.ui.View):
    """Класс представления с кнопками действий игрока"""
    
    def __init__(self, game: BunkerGame, player: Player):
        """
        Инициализация представления для действий игрока
        
        Args:
            game: Объект игры
            player: Объект игрока
        """
        super().__init__(timeout=None)
        self.game = game
        self.player = player
        
        # Добавление кнопок для раскрытия характеристик
        characteristics = [
            ("Пол", "gender"),
            ("Телосложение", "body"),
            ("Черта", "trait"),
            ("Профессия", "profession"),
            ("Здоровье", "health"),
            ("Хобби", "hobby"),
            ("Фобия", "phobia"),
            ("Инвентарь", "inventory"),
            ("Рюкзак", "backpack"),
            ("Доп. сведение", "additional"),
        ]
        
        for label, attr in characteristics:
            self.add_item(RevealButton(label, attr))
        
        # Кнопка для специальной возможности
        self.add_item(SpecialAbilityButton(self.game, self.player))

# Кнопка для использования специальной способности
class SpecialAbilityButton(discord.ui.Button):
    """Кнопка для использования специальной способности игрока"""
    
    def __init__(self, game: BunkerGame, player: Player):
        """
        Инициализация кнопки
        
        Args:
            game: Объект игры
            player: Объект игрока
        """
        super().__init__(
            label="Использовать спец. возможность", 
            style=discord.ButtonStyle.danger, 
            custom_id="special_ability",
            row=4
        )
        self.game = game
        self.player = player
        self.used = False
    
    async def callback(self, interaction: discord.Interaction):
        """Обработчик нажатия на кнопку специальной способности"""
        try:
            # Отложенный ответ
            await interaction.response.defer(ephemeral=True)
            
            # Проверка, что способность еще не использована
            if self.used:
                await interaction.followup.send("Вы уже использовали свою специальную возможность!", ephemeral=True)
                return
            
            # Проверка, что игра активна
            if self.game.status != "running":
                await interaction.followup.send("Игра еще не началась или уже завершена!", ephemeral=True)
                return
            
            # Отправка сообщения с информацией о способности
            await interaction.followup.send(
                f"Ваша специальная возможность: **{self.player.special_ability}**\n\n"
                "Способность будет применена в ближайшее время. Следите за сообщениями в общем канале.",
                ephemeral=True
            )
            
            # Уведомление в канал
            channel = bot.get_channel(self.game.channel_id)
            await channel.send(f"**{self.player.name}** использует свою специальную возможность!")
            
            # Деактивация кнопки
            self.used = True
            self.disabled = True
            await interaction.message.edit(view=self.view)
            logger.info(f"Игрок {self.player.name} использовал специальную возможность: {self.player.special_ability}")
        except Exception as e:
            logger.error(f"Ошибка при использовании спец. возможности: {e}", exc_info=True)
            await interaction.followup.send(f"Произошла ошибка: {e}", ephemeral=True)

# Кнопка для раскрытия характеристики
class RevealButton(discord.ui.Button):
    """Кнопка для раскрытия характеристики игрока"""
    
    def __init__(self, label: str, attribute: str):
        """
        Инициализация кнопки
        
        Args:
            label: Метка кнопки
            attribute: Имя атрибута для раскрытия
        """
        super().__init__(
            label=f"Открыть {label.lower()}", 
            style=discord.ButtonStyle.secondary, 
            custom_id=f"reveal_{attribute}"
        )
        self.attribute = attribute
    
    async def callback(self, interaction: discord.Interaction):
        """Обработчик нажатия на кнопку раскрытия характеристики"""
        try:
            # Отложенный ответ
            await interaction.response.defer(ephemeral=True)
            
            # Получение игры и игрока из контекста
            game = None
            player = None
            
            for g in active_games.values():
                for p in g.players:
                    if p.id == interaction.user.id:
                        game = g
                        player = p
                        break
                if game:
                    break
            
            if not game or not player:
                await interaction.followup.send("Ошибка: игра не найдена", ephemeral=True)
                return
            
            # Раскрытие характеристики
            if player.reveal_attribute(self.attribute):
                # Обновление у всех игроков
                await game.update_all_player_tables(bot)
                
                # Уведомление в канале
                channel = bot.get_channel(game.channel_id)
                attribute_name = self.label.replace('Открыть ', '')
                await channel.send(f"**{player.name}** раскрыл характеристику: **{attribute_name}**")
                
                # await interaction.followup.send(f"Вы раскрыли характеристику: {attribute_name}", ephemeral=True)
                
                # Деактивация кнопки
                self.disabled = True
                await interaction.message.edit(view=self.view)
                logger.info(f"Игрок {player.name} раскрыл характеристику: {attribute_name}")
            else:
                await interaction.followup.send("Эта характеристика уже раскрыта!", ephemeral=True)
        except Exception as e:
            logger.error(f"Ошибка при раскрытии характеристики: {e}", exc_info=True)
            await interaction.followup.send(f"Произошла ошибка: {e}", ephemeral=True)

# Запуск бота
if __name__ == "__main__":
    try:
        logger.info("Запуск бота...")
        bot.run(TOKEN)
    except Exception as e:
        logger.critical(f"Не удалось запустить бота: {e}", exc_info=True) 