from typing import List, Dict, Any, Optional

class AIClient:
    """Base class for working with LLM."""
    
    def __init__(self, model: str = None, provider: Any = None, image_model: str = None, image_provider: Any = None):
        self.model = model
        self.provider = provider
        self.image_model = image_model
        self.image_provider = image_provider
    
    async def generate_message(self, messages: List[Dict[str, str]]) -> str:
        """
        Generates an answer from the model based on messages.
        
        Args:
            messages: List of messages in the format [{"role": "...", "content": "..."}]
            
        Returns:
            str: Model answer
        """
        raise NotImplementedError("Subclasses must implement generate_message")

    async def generate_image(self, prompt: str) -> str:
        """
        Generates an image from the model based on prompt.
        """
        raise NotImplementedError("Subclasses must implement generate_image")



class G4FClient(AIClient):
    """Client for working with g4f."""
    
    def __init__(self, model: str, provider: Any, image_model: str, image_provider: Any):
        super().__init__(model, provider, image_model, image_provider)
        from g4f.client import AsyncClient
        self.client = AsyncClient(provider=provider)
        self.image_client = AsyncClient(provider=image_provider)
    
    async def generate_message(self, messages: List[Dict[str, str]]) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages
        )
        return response.choices[0].message.content 
    
    async def generate_image(self, prompt: str) -> str:
        response = await self.image_client.images.generate(
            model=self.image_model,
            prompt=prompt,
            response_format="url"
        )
        return response.data[0].url
    
