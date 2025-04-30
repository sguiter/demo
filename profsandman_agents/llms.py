from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, Union

import openai
from pydantic import BaseModel

from profsandman_agents.token_counters import OpenAITokenCounter

# ==============================================================
# Constants
# ==============================================================

# Token limits for different OpenAI models
# https://platform.openai.com/docs/models
OPENAI_TOKEN_LIMITS = {
    "gpt-4": 32768,
    "gpt-4-turbo": 131072,
    'gpt-4o': 128000,
    'gpt-4o-mini': 128000,
    'o3-mini': 200000
}

# Safety limit to allow for system prompts and other metadata
SAFETY_LIM = 1000

# Default model parameters
DEFAULTS = {
    'model': 'gpt-4o-mini',
    'temperature': 1,
}

# ==============================================================
# Abstract Base Classes
# ==============================================================

class BaseLLM(ABC):
    """
    Abstract base class for large language model implementations.
    
    This class defines the interface for interacting with different LLM providers,
    supporting both free-form text queries and structured responses.
    """
    @abstractmethod
    def __init__(self, model_args: Dict[str, Any], **kwargs) -> None:
        """
        Initialize the language model.
        
        Args:
            model_args: Dictionary containing model configuration parameters
            **kwargs: Additional keyword arguments
        """
        pass

    @abstractmethod
    def query(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Send a query to the language model and get a text response.
        
        Args:
            prompt: The user's prompt
            system_prompt: Optional system prompt to set context
            
        Returns:
            The model's response as text
        """
        pass
    
    @abstractmethod
    def structured_query(self, response_format: Type[BaseModel], prompt: str, 
                         system_prompt: Optional[str] = None) -> BaseModel:
        """
        Send a query to the language model and get a structured response.
        
        Args:
            response_format: Pydantic model defining the expected response structure
            prompt: The user's prompt
            system_prompt: Optional system prompt to set context
            
        Returns:
            The model's response parsed into the specified Pydantic model
        """
        pass


# ==============================================================
# OpenAI
# ==============================================================

class OpenAILLM(BaseLLM):
    """
    OpenAI Large Language Model implementation.
    
    This class provides an interface to OpenAI's language models like GPT-4, GPT-4o, etc.
    It handles token counting, model validation, and both standard and structured queries.
    
    Attributes:
        client_: OpenAI client instance
        model_args_: Dictionary of model parameters
        token_counter_: Counter for tracking token usage
    """

    def __init__(self, api_key: str, model_args: Dict[str, Any] = DEFAULTS, **kwargs) -> None:
        """
        Initialize the OpenAI LLM.
        
        Args:
            api_key: OpenAI API key
            model_args: Dictionary containing model configuration parameters:
                - model: The OpenAI model to use (e.g., 'gpt-4o', 'gpt-4-turbo')
                - temperature: Controls randomness in responses (0.0-2.0)
                - max_tokens: Maximum tokens in the response (optional)
            **kwargs: Additional arguments
            
        Raises:
            ValueError: If model is not specified or not supported
        """
        self.client_ = openai.OpenAI(api_key=api_key)
        self.model_args_ = model_args
        
        if "model" not in model_args:
            raise ValueError("model must be specified in the model_args.")
        
        self._check_model_exists(model_args['model'])
        self.token_counter_ = OpenAITokenCounter(model=model_args['model'])

    def _check_model_exists(self, model: str) -> bool:
        """
        Check if the model is supported by this implementation.
        
        Args:
            model: The model name to check
            
        Returns:
            True if model exists
            
        Raises:
            ValueError: If model is not supported
        """
        if model not in OPENAI_TOKEN_LIMITS:
            raise ValueError(f"Model {model} not supported. Please use a supported model.")
        return True

    def _check_token_limit(self, text: str) -> bool:
        """
        Check if the text is within the token limit for the selected model.
        
        Args:
            text: The text to check
            
        Returns:
            True if text is within token limit
            
        Raises:
            ValueError: If text exceeds token limit
        """
        token_count = self.token_counter_.count_tokens(text)
        model_limit = OPENAI_TOKEN_LIMITS[self.model_args_['model']]
        if token_count + SAFETY_LIM > model_limit:
            raise ValueError(f"Text is too long for the model. Token count: {token_count}, limit: {model_limit}.")
        return True

    def _build_message(self, prompt: Union[str, List[Dict[str, str]]], 
                       system_prompt: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Build the message structure for the OpenAI API.
        
        Args:
            prompt: Either a string prompt or a list of message dictionaries
            system_prompt: System prompt to set context for the model
            
        Returns:
            Properly formatted messages for the OpenAI API
        """
        # Set default system prompt if none provided
        if system_prompt is None:
            system_prompt = "You are a helpful AI assistant."
            
        # Build response (single shot prompt vs ongoing conversation)
        if isinstance(prompt, str):
            message = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        else:
            message = prompt
            
        return message

    def query(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Send a query to the OpenAI model and get a text response.
        
        Args:
            prompt: The user's prompt
            system_prompt: System prompt to set context
            
        Returns:
            The model's response text
            
        Raises:
            ValueError: If prompt exceeds token limit
        """
        self._check_token_limit(prompt)
        message = self._build_message(prompt, system_prompt)
        response = self.client_.chat.completions.create(messages=message, **self.model_args_)
        return response.choices[0].message.content
    
    def structured_query(self, response_format: Type[BaseModel], prompt: str, 
                         system_prompt: Optional[str] = None) -> BaseModel:
        """
        Send a query to the OpenAI model and get a structured response.
        
        Args:
            response_format: Pydantic model defining the expected response structure
            prompt: The user's prompt
            system_prompt: System prompt to set context
            
        Returns:
            The model's response parsed into the specified Pydantic model
            
        Raises:
            ValueError: If prompt exceeds token limit
        """
        self._check_token_limit(prompt)
        message = self._build_message(prompt, system_prompt)
        response = self.client_.beta.chat.completions.parse(
            messages=message,
            response_format=response_format,
            **self.model_args_
        )
        return response.choices[0].message.parsed