"""
LLM Client - Interface for multiple LLM providers
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional
import httpx
import os
import asyncio

# Cerebras SDK (chat completions client)
try:
    from cerebras.cloud.sdk import Cerebras
except ImportError:
    # Fallback for older/newer SDK layouts; will raise at runtime if actually used
    Cerebras = None

# Google Generative AI SDK
try:
    import google.generativeai as genai
except ImportError:
    genai = None


class LLMProvider(Enum):
    """Supported LLM providers."""
    HUGGINGFACE = "huggingface"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"
    CEREBRAS = "cerebras"
    GOOGLE = "google"
    GROQ = "groq"


class LLMClient(ABC):
    """Base class for LLM clients."""
    
    @abstractmethod
    async def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        """Generate a response from the LLM."""
        pass


class HuggingFaceClient(LLMClient):
    """Hugging Face Inference API client."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "mistralai/Mistral-7B-Instruct-v0.2"):
        self.api_key = api_key or os.getenv("HUGGINGFACE_API_KEY")
        self.model = model
        self.base_url = "https://api-inference.huggingface.co/models"
    
    async def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        """Generate using Hugging Face API."""
        if not self.api_key:
            # Fallback to a free model that doesn't require auth
            return await self._generate_free(prompt)
        
        url = f"{self.base_url}/{self.model}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": 0.7,
                "return_full_text": False
            }
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                
                # Handle different response statuses
                if response.status_code == 503:
                    # Model is loading, wait and retry
                    print(f"Model {self.model} is loading, using fallback")
                    return await self._generate_free(prompt)
                
                response.raise_for_status()
                result = response.json()
                
                # Handle error responses from HuggingFace
                if isinstance(result, dict) and "error" in result:
                    print(f"HuggingFace API error: {result.get('error')}")
                    return await self._generate_free(prompt)
                
                if isinstance(result, list) and len(result) > 0:
                    generated = result[0].get('generated_text', '')
                    if generated:
                        return generated
                elif isinstance(result, dict):
                    generated = result.get('generated_text', '')
                    if generated:
                        return generated
                
                # If no generated text found, try fallback
                return await self._generate_free(prompt)
                
            except httpx.TimeoutException:
                print("HuggingFace API timeout, using fallback")
                return await self._generate_free(prompt)
            except httpx.HTTPStatusError as e:
                print(f"HuggingFace API HTTP error {e.response.status_code}: {e}")
                return await self._generate_free(prompt)
            except Exception as e:
                print(f"HuggingFace API error: {e}")
                # Fallback to free model
                return await self._generate_free(prompt)
    
    async def _generate_free(self, prompt: str) -> str:
        """Use a free model that doesn't require authentication."""
        # Try multiple free models that work without auth
        free_models = [
            "microsoft/DialoGPT-medium",
            "gpt2",
            "distilgpt2"
        ]
        
        for model in free_models:
            url = f"https://api-inference.huggingface.co/models/{model}"
            
            payload = {
                "inputs": prompt[:512] if model == "microsoft/DialoGPT-medium" else prompt[:1024],
                "parameters": {
                    "max_new_tokens": 500,
                    "temperature": 0.7,
                    "return_full_text": False
                }
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                try:
                    response = await client.post(url, json=payload)
                    if response.status_code == 200:
                        result = response.json()
                        if isinstance(result, list) and len(result) > 0:
                            generated = result[0].get('generated_text', '')
                            if generated:
                                return generated
                        elif isinstance(result, dict):
                            generated = result.get('generated_text', '')
                            if generated:
                                return generated
                except Exception as e:
                    print(f"Error with model {model}: {e}")
                    continue
        
        # Ultimate fallback: return a mock structured response
        # This ensures the system doesn't crash but warns the user
        return """[
  {"id": 1, "name": "Sample Factor", "description": "This is a placeholder response. Please configure an LLM API key for full functionality."}
]"""


class OpenRouterClient(LLMClient):
    """OpenRouter API client (supports multiple free models)."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "google/gemini-flash-1.5"):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
    
    async def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        """Generate using OpenRouter API."""
        if not self.api_key:
            raise ValueError("OpenRouter API key required. Set OPENROUTER_API_KEY environment variable.")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/project-aether",
            "X-Title": "Project AETHER"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(self.base_url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            return result['choices'][0]['message']['content']


class OllamaClient(LLMClient):
    """Ollama client for local models."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama2"):
        self.base_url = base_url
        self.model = model
    
    async def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        """Generate using local Ollama."""
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": 0.7
            }
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()
                return result.get('response', '')
            except Exception as e:
                return f"[Ollama Error: {str(e)}]"


class CerebrasClient(LLMClient):
    """Cerebras Inference API client (via cerebras-cloud-sdk)."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        # Read config from env with sensible defaults
        if Cerebras is None:
            raise ImportError(
                "Cerebras SDK not available. Install with 'pip install cerebras-cloud-sdk' "
                "and ensure the version supports 'from cerebras.cloud.sdk import Cerebras'."
            )

        self.api_key = api_key or os.getenv("CEREBRAS_API_KEY")
        if not self.api_key:
            raise ValueError("Cerebras API key required. Set CEREBRAS_API_KEY environment variable.")
        
        # Default to a common, reasonably small model if none is provided
        self.model = model or os.getenv("CEREBRAS_MODEL", "llama3.1-8b")
        # Initialize Cerebras SDK client (sync client)
        self.client = Cerebras(api_key=self.api_key)
    
    async def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        """Generate using Cerebras chat completions (run sync client in a thread)."""
        
        def _call_cerebras():
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7,
            )
            # Response is OpenAI-style; extract the first choice content
            return response.choices[0].message.content
        
        try:
            return await asyncio.to_thread(_call_cerebras)
        except Exception as e:
            return f"[Cerebras Error: {str(e)}]"


class GoogleClient(LLMClient):
    """Google Gemini API client."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-pro"):
        if genai is None:
            raise ImportError(
                "Google Generative AI SDK not available. Install with 'pip install google-generativeai'"
            )
        
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google API key required. Set GOOGLE_API_KEY environment variable.")
        
        self.model_name = model
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
    
    async def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        """Generate using Google Gemini API."""
        
        def _call_gemini():
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.7,
                )
            )
            return response.text
        
        try:
            return await asyncio.to_thread(_call_gemini)
        except Exception as e:
            return f"[Google Gemini Error: {str(e)}]"


class GroqClient(LLMClient):
    """Groq API client for fast inference."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Groq API key required. Set GROQ_API_KEY environment variable.")
        
        self.model = model
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
    
    async def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        """Generate using Groq API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(self.base_url, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                return result['choices'][0]['message']['content']
            except Exception as e:
                return f"[Groq Error: {str(e)}]"


def create_llm_client(provider: LLMProvider = LLMProvider.HUGGINGFACE, **kwargs) -> LLMClient:
    """Factory function to create LLM client."""
    if provider == LLMProvider.HUGGINGFACE:
        return HuggingFaceClient(**kwargs)
    elif provider == LLMProvider.OPENROUTER:
        return OpenRouterClient(**kwargs)
    elif provider == LLMProvider.OLLAMA:
        return OllamaClient(**kwargs)
    elif provider == LLMProvider.CEREBRAS:
        return CerebrasClient(**kwargs)
    elif provider == LLMProvider.GOOGLE:
        return GoogleClient(**kwargs)
    elif provider == LLMProvider.GROQ:
        return GroqClient(**kwargs)
    else:
        raise ValueError(f"Unknown provider: {provider}")
