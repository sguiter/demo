from abc import ABC, abstractmethod
from typing import List, Union

import numpy as np
from sentence_transformers import SentenceTransformer
import tqdm

# ==============================================================
# Strategy Pattern
# ==============================================================

class BaseEmbedder(ABC):
    """
    Abstract base class for text embedding strategies.
    
    This class defines the interface for embedding text into vector representations
    that can be used for semantic search and similarity comparisons.
    """
    @abstractmethod
    def embed(self, text: Union[str, List[str], List[List[str]]]) -> List[List[List[float]]]:
        """
        Convert text into vector embeddings.
        
        Args:
            text: Input text to embed. Can be:
                - A single string
                - A list of strings (chunks)
                - A list of lists of strings (documents with chunks)
                
        Returns:
            A list of lists of lists of floats representing the embeddings.
            The structure follows: [documents][chunks][embedding_dimensions]
        """
        pass

# ==============================================================
# Sentence Transformer Embedder
# ==============================================================

class SentenceTransformerEmbedder(BaseEmbedder):
    """
    Text embedder implementation using the SentenceTransformer library.
    
    This class provides methods to convert text into vector embeddings
    using pre-trained sentence transformer models.
    """
    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        """
        Initialize the SentenceTransformer embedder.
        
        Args:
            model_name: Name of the pre-trained model to use.
                Default is "all-MiniLM-L6-v2", a lightweight general-purpose model.
        """
        self.model_ = SentenceTransformer(model_name)

    def embed(self, text: Union[str, List[str], List[List[str]]]) -> List[List[List[float]]]:
        """
        Convert text into vector embeddings using SentenceTransformer.
        
        Args:
            text: Input text to embed. Can be:
                - A single string
                - A list of strings (chunks)
                - A list of lists of strings (documents with chunks)
                
        Returns:
            A list of lists of lists of floats representing the embeddings.
            The structure follows: [documents][chunks][embedding_dimensions]
            
        Raises:
            ValueError: If the input format is not recognized
        """
        # Convert text to ensure it follows Document-List[Chunk-List[Vector-List[float]]]
        if isinstance(text, str):
            text = [[text]]  # Convert single string to a list of lists (1 document, 1 chunk)
        elif isinstance(text, list) and isinstance(text[0], str):
            text = [text]  # Convert a list of strings (1 document) into a list of lists
        elif not (isinstance(text, list) and isinstance(text[0], list)):
            raise ValueError("Input must be a string, a list of strings (chunks), or a list of lists of strings (documents with chunks).")

        docs = []
        # for doc in tqdm.tqdm(text, desc="Embedding documents", unit="document"):
        for doc in text:
            chunk_embeddings = self.model_.encode(doc).tolist()  # Ensure embeddings are returned as a list
            docs.append(chunk_embeddings)

        return docs