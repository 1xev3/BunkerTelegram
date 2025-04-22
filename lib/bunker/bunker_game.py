from collections.abc import AsyncGenerator
import logging
from typing import List, Dict, Optional

from lib.ai_client import G4FClient
from lib.bunker.player import Player
from lib.bunker.bunker import Bunker
from lib.bunker.image_generator import ImageGenerator

class BunkerGame:
    """Base class for bunker game logic"""
    
    def __init__(self, ai_client: G4FClient):
        """
        Initialize the game
        
        Args:
            ai_client: AI client for generating content
        """
        self.ai_client = ai_client
        self.status = "waiting"  # waiting, running, finished
        self.players: List[Player] = []
        self.bunker = Bunker(self.ai_client)
        self.current_round = 0
        self.votes = {}  # {voter_id: voted_for_id}
        self.voted_players = set()  # Set of players who have voted
        self.active_voting_players = 0  # Counter of active voting players
    
    def add_player(self, player: Player) -> None:
        """
        Add player to the game
        
        Args:
            player: Player object
        """
        self.players.append(player)
    
    def remove_player(self, player_id: int) -> bool:
        """
        Remove player from the game
        
        Args:
            player_id: ID of player to remove
            
        Returns:
            bool: True if player was removed, False if player not found
        """
        for player in self.players:
            if player.id == player_id:
                player.is_active = False
                return True
        return False
    
    async def generate_bunker(self, theme: str = None):
        """Generate bunker"""
        async for status_msg in self.bunker.generate(theme):
            logging.info(status_msg)
            yield status_msg
    
    async def generate_player_cards(self) -> AsyncGenerator[str, None]:
        """Generate cards for all players"""
        for player in self.players:
            async for status_msg in player.generate_character(self.ai_client):
                logging.info(status_msg)
                yield f"Игрок {player.name}: {status_msg}"
    
    def generate_status_image(self) -> bytes:
        """
        Generate status table image
        
        Returns:
            bytes: Image bytes of status table
        """
        return ImageGenerator.generate_status_image(self.players)
    
    def next_round(self) -> int:
        """
        Move to next round
        
        Returns:
            int: New round number
        """
        self.current_round += 1
        return self.current_round
    
    def get_active_players(self) -> List[Player]:
        """
        Get list of active players
        
        Returns:
            List[Player]: List of active players
        """
        return [player for player in self.players if player.is_active]
    
    def get_player_by_id(self, player_id: int) -> Optional[Player]:
        """
        Get player by ID
        
        Args:
            player_id: Player ID
            
        Returns:
            Optional[Player]: Player object or None if not found
        """
        for player in self.players:
            if player.id == player_id:
                return player
        return None
    
    def reset_votes(self) -> None:
        """Reset votes"""
        self.votes = {}
        self.voted_players = set()
    
    def add_vote(self, voter_id: int, target_id: int) -> bool:
        """
        Add vote
        
        Args:
            voter_id: ID of voting player
            target_id: ID of player being voted for
            
        Returns:
            bool: True if vote was counted, False if player already voted
        """
        if voter_id in self.voted_players:
            return False
        
        self.votes[voter_id] = target_id
        self.voted_players.add(voter_id)
        return True
    
    def count_votes(self) -> Dict[int, int]:
        """
        Count votes
        
        Returns:
            Dict[int, int]: Dictionary {player_id: vote_count}
        """
        results = {}
        for target_id in self.votes.values():
            results[target_id] = results.get(target_id, 0) + 1
        return results

    async def end_game(self, winner=None, reason="") -> None:
        """
        End the game
        
        Args:
            winner: Optional winner player object
            reason: Reason for game ending
        """
        self.status = "finished"
        
        # Reveal all attributes for all players
        for player in self.players:
            for attribute in ["gender", "body", "trait", "profession", "health", 
                            "hobby", "phobia", "inventory", "backpack", "additional"]:
                player.reveal_attribute(attribute)

    async def analyze_bunker_survival(self) -> str:
        """
        Analyze bunker survival chances with current players
        
        Returns:
            str: Analysis text
        """
        try:
            # Get active players
            active_players = self.get_active_players()
            if not active_players:
                return "Некому выживать в бункере!"
            
            # Get bunker info
            bunker_info = self.bunker.get_description()
            
            # Form player info
            survivors_info = []
            for i, player in enumerate(active_players, 1):
                player_card = player.get_character_card()
                survivors_info.append(f"**Игрок {i}: {player.name}**\n{player_card}")
            
            survivors_text = "\n\n".join(survivors_info)
            
            # Form prompt
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
            
            # Get AI analysis
            survival_analysis = await self.ai_client.generate_message([
                {"role": "system", "content": "Ты эксперт по выживанию. Анализируешь шансы выжить группе людей в бункере в условиях постапокалипсиса. Отвечай подробно, учитывай совместимость профессий, навыков и особенностей людей."},
                {"role": "user", "content": prompt}
            ])
            
            return survival_analysis
        except Exception as e:
            logging.error(f"Error analyzing bunker survival: {e}")
            return f"Произошла ошибка при анализе выживания: {e}" 