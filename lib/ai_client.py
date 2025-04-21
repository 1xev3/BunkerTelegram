from typing import List, Dict, Any, Optional
import base64
import io
from PIL import Image

from lib.sd_api.api_models import txt2img_params
from lib.sd_api.sd_api import WebUIApi

import logging

logger = logging.getLogger("ai_client")

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

    async def generate_image(self, prompt: str) -> Image.Image:
        """
        Generates an image from the model based on prompt.
        """
        raise NotImplementedError("Subclasses must implement generate_image")



class G4FClient(AIClient):
    """Client for working with g4f."""
    
    def __init__(self, model: str, provider: Any, image_model: str, image_provider: Any, proxies: str = None):
        super().__init__(model, provider, image_model, image_provider)
        from g4f.client import AsyncClient
        self.client = AsyncClient(provider=provider, proxies=proxies)
        self.image_client = AsyncClient(provider=image_provider)
    
    async def generate_message(self, messages: List[Dict[str, str]]) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages
        )
        return response.choices[0].message.content 
    
    # async def generate_image(self, prompt: str) -> Image.Image:
    #     response = await self.image_client.images.generate(
    #         model=self.image_model,
    #         prompt=prompt,
    #         response_format="b64_json"
    #     )
    #     # Convert base64 to PIL Image
    #     image_bytes = base64.b64decode(response.data[0].b64_json)
    #     image = Image.open(io.BytesIO(image_bytes))
    #     return image

    async def generate_image(self, prompt: str) -> Image.Image:

        try:
            api = WebUIApi()
            params = txt2img_params()
            params.prompt = f"masterpiece,best quality,amazing quality, {prompt}"
            params.negative_prompt = "bad quality, worst quality, worst detail, censor, signature"
            params.width = 1216
            params.height = 832
            params.batch_size = 1
            params.n_iter = 1
            
            result = await api.txt2img(params)
            return result.image
        except Exception as e:
            logger.error(f"Error generating image: {e}")

            response = await self.image_client.images.generate(
                model=self.image_model,
                prompt=prompt,
                response_format="b64_json"
            )
            # Convert base64 to PIL Image
            image_bytes = base64.b64decode(response.data[0].b64_json)
            image = Image.open(io.BytesIO(image_bytes))
            return image
    
    
