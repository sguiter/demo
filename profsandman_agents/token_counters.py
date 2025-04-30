from abc import ABC, abstractmethod
from typing import Dict, Optional, Union

# ==============================================================
# Abstract Base Classes
# ==============================================================

class BaseTokenCounter(ABC):
    """
    Abstract base class for token counting strategies.
    
    This class defines the interface for counting tokens in text,
    which is important for managing context windows in LLM interactions.
    """
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text string.
        
        Args:
            text: The text to count tokens for
            
        Returns:
            The number of tokens in the text
        """
        pass

# ==============================================================
# OpenAI
# ==============================================================

import tiktoken

class OpenAITokenCounter(BaseTokenCounter):
    """
    A token counter for OpenAI models using tiktoken.
    
    Automatically selects the correct encoding based on the model.
    """
    def __init__(self, model: str = "gpt-4o-mini") -> None:
        """
        Initialize the token counter.
        
        Args:
            model: The OpenAI model to use for token counting. Defaults to "gpt-4o-mini".
        """
        self.model_: str = model
        self.enc_ = tiktoken.encoding_for_model(model)

    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text string using OpenAI's tiktoken.
        
        Args:
            text: The text to count tokens for
            
        Returns:
            The number of tokens in the text
        """
        return len(self.enc_.encode(text))
