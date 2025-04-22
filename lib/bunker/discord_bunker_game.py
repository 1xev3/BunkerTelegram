import discord
import logging
import re
from typing import Optional

from lib.bunker.bunker_game import BunkerGame
from lib.bunker.game_config import GameConfig
from lib.bunker.player import Player

class DiscordBunkerGame(BunkerGame):
    """Discord-specific implementation of BunkerGame"""
    
    def __init__(self, ai_client, admin_id: int, channel_id: int):
        """
        Initialize Discord game
        
        Args:
            ai_client: AI client for generating content
            admin_id: ID of game admin
            channel_id: ID of Discord channel where game is played
        """
        super().__init__(ai_client)
        self.admin_id = admin_id
        self.channel_id = channel_id
        self.message_id = None
        self.admin_message_id = None
        self.vote_message_id = None
    
    async def end_game(self, bot, winner: Optional[Player] = None, reason: str = "") -> None:
        """
        End the game with Discord-specific notifications
        
        Args:
            bot: Discord bot instance
            winner: Optional winner player
            reason: Reason for game ending
        """
        try:
            logger = logging.getLogger('bunker_game')
            
            # Call parent end_game to handle game logic
            await super().end_game(winner, reason)
            
            # Get channel
            channel = bot.get_channel(self.channel_id)
            if not channel:
                logger.error(f"Error: channel {self.channel_id} not found when ending game")
                return
            
            # Send final status table
            status_image_bytes = self.generate_status_image()
            status_image = discord.File(status_image_bytes, filename='status.png')
            await channel.send("📊 Финальная таблица всех игроков:", file=status_image)
            
            # Send winner notification if exists
            if winner:
                winner_embed = discord.Embed(
                    title="🏆 Игра завершена!",
                    description=f"**{winner.name}** - единственный выживший в бункере! Поздравляем с победой!",
                    color=discord.Color.gold()
                )
                await channel.send(embed=winner_embed)
                
                # Send DM to winner
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
                    logger.error(f"Error sending winner notification: {e}")
            else:
                # Send game end notification
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
            
            # Remove game from active games
            try:
                import sys
                main_module = sys.modules.get('__main__')
                if hasattr(main_module, 'active_games') and self.channel_id in main_module.active_games:
                    del main_module.active_games[self.channel_id]
                    logger.info(f"Game removed from active games in channel {self.channel_id}")
            except Exception as e:
                logger.error(f"Failed to remove game from active games: {e}")
            
            logger.info(f"Game in channel {self.channel_id} ended" + (f": {reason}" if reason else ""))
            
            if GameConfig.GENERATE_ANALYSIS:
                await self.analyze_bunker_survival_discord(bot)
        except Exception as e:
            logger.error(f"Error ending game: {e}")
    
    async def analyze_bunker_survival_discord(self, bot) -> None:
        """
        Analyze bunker survival and send results to Discord channel
        
        Args:
            bot: Discord bot instance
        """
        try:
            channel = bot.get_channel(self.channel_id)
            if not channel:
                return
            
            # Send analyzing message
            analyzing_message = await channel.send("🔍 Анализирую шансы выживания обитателей бункера...")
            
            # Get analysis from parent class
            analysis_text = await self.analyze_bunker_survival()
            
            # Delete analyzing message
            try:
                await analyzing_message.delete()
            except:
                pass
            
            # Send results
            await self._send_analysis_results(channel, analysis_text)
        except Exception as e:
            logger = logging.getLogger('bunker_game')
            logger.error(f"Error analyzing bunker survival: {e}")
            try:
                await channel.send(f"Произошла ошибка при анализе выживания: {e}")
            except:
                pass
    
    async def _send_analysis_results(self, channel, analysis_text):
        """
        Send analysis results to Discord channel, splitting into multiple messages if needed
        
        Args:
            channel: Discord channel to send to
            analysis_text: Analysis text from AI
        """
        MAX_EMBED_LENGTH = 1000
        title = "🔍 Анализ выживания в бункере"
        
        if len(analysis_text) <= MAX_EMBED_LENGTH:
            embed = discord.Embed(
                title=title,
                description=analysis_text,
                color=discord.Color.blue()
            )
            await channel.send(embed=embed)
        else:
            # Split text into sentences
            sentences = re.split(r'(?<=[.!?]) +', analysis_text)
            parts = []
            current_part = ""
            
            for sentence in sentences:
                if len(sentence) > MAX_EMBED_LENGTH:
                    if current_part:
                        parts.append(current_part)
                        current_part = ""
                    
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
                    if len(current_part) + len(sentence) + 1 > MAX_EMBED_LENGTH:
                        parts.append(current_part)
                        current_part = sentence
                    else:
                        if current_part:
                            current_part += " " + sentence
                        else:
                            current_part = sentence
            
            if current_part:
                parts.append(current_part)
            
            # Send each part
            for i, part in enumerate(parts):
                part_title = f"{title} (Часть {i+1}/{len(parts)})"
                embed = discord.Embed(
                    title=part_title,
                    description=part,
                    color=discord.Color.blue()
                )
                await channel.send(embed=embed) 