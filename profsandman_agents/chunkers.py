from abc import ABC, abstractmethod
from math import ceil
from typing import Dict, List, Optional, Tuple, Union

import tiktoken
from llama_index.core.node_parser import SentenceSplitter, SentenceWindowNodeParser
from pydantic import BaseModel
from tqdm import tqdm

from profsandman_agents.llms import BaseLLM, OPENAI_TOKEN_LIMITS
from profsandman_agents.token_counters import OpenAITokenCounter

# ==============================================================
# Constants
# ==============================================================

# Safety divisor to ensure we get all input text back in structured outputs from the LLM
SAFETY_DIVISOR = 4

# Target token count for chunks
DESIRED_CHUNK_TOKENS = 450

# System prompt for semantic chunking
SYSTEM_PROMPT = """You are an advanced text-processing AI designed to split a body of text into optimally sized chunks while preserving semantic coherence and contextual relevance. The goal is to create chunks that maximize retrieval accuracy while ensuring each chunk remains a self-contained, meaningful unit."""

# Base prompt for semantic chunking
PROMPT_BASE = """## Objective:
Split the following text into optimally sized chunks while preserving semantic coherence and contextual relevance for the sake of retrieval-augmented generation (RAG).

## Ideal Chunk Definition:
The ideal chunk is one that is large enough to provide sufficient context for retrieval yet small enough to maximize relevance and minimize noise. 
The chunk should be semantically coherent, meaning it should encapsulate a complete thought, topic, or logical section of the text.

## Instructions  

### 1. Chunk Size Considerations  
- Prioritize **paragraph-level** segmentation.  
- If a section is too long, intelligently break it at logical stopping points (e.g., sentence transitions, topic shifts).  

### 2. Preserving Context & Meaning  
- Ensure that **definitions, examples, and explanations remain together** in a single chunk.  
- Keep **lists, tables, or code snippets intact** with their explanations.  

### 3. Return Format  
- Return a **list of strings**, where each string is a chunk.
"""

# ==============================================================
# Abstract Base Classes
# ==============================================================

class BaseChunker(ABC):
    """
    Abstract base class for text chunking strategies.
    
    This class defines the interface for splitting text into smaller chunks
    that can be processed by embedding models and vector databases.
    """
    @abstractmethod
    def __init__(self, **kwargs):
        """
        Initialize the chunker.
        """
        pass

    @abstractmethod
    def chunk(self, text: Union[str, List[str]]) -> List[List[str]]:
        """
        Split text into chunks.
        
        Args:
            text: The input text to be chunked. Can be a single string or a list of strings.
            
        Returns:
            A list of lists of strings, where each inner list represents chunks for a document.
        """
        pass

# ==============================================================
# Naive Chunking
# ==============================================================

class SplitCharChunker(BaseChunker):
    """
    A chunker that splits text based on a specific character sequence.
    
    This is a simple chunking strategy that works well for text with
    clear delimiters like paragraphs separated by blank lines.
    """
    def __init__(self, split_char: str = "\n\n"):
        """
        Initialize the chunker.

        Args:
            split_char: The character sequence to split the text on. Defaults to paragraph breaks.
        """
        self.split_char_ = split_char

    def chunk(self, text: Union[str, List[str]]) -> List[List[str]]:
        """
        Split text into chunks based on a specific character.

        Args:
            text: The input text to be chunked. Can be a single string or a list of strings.
            
        
        Returns:
            A list of lists of strings, where each inner list represents chunks for a document.
        """
        if isinstance(text, str):
            text = [text]
        
        docs = []
        for t in tqdm(text, desc="Splitting text by character", unit="document"):
            chunks = t.split(self.split_char_)
            docs.append(chunks)
        return docs

class CharLenChunker(BaseChunker):
    """
    A chunker that splits text based on character length with overlap.
    
    This chunker uses recursive sentence splitting to ensure chunks don't
    break in the middle of sentences. Best suited for unstructured text.
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        """
        Initialize the chunker.

        Args:
            chunk_size: Target size of characters for each chunk.
            overlap: Number of characters to overlap between chunks.
        """
        self.chunk_size_ = chunk_size
        self.overlap_ = overlap

    def chunk(self, text: Union[str, List[str]]) -> List[List[str]]:
        """
        Split text into chunks using recursive sentence splitting.
        
        Args:
            text: The input text to be chunked. Can be a single string or a list of strings.
        
        Returns:
            A list of lists of strings, where each inner list represents chunks for a document.
        """
        if isinstance(text, str):
            text = [text]        
        
        text_splitter = SentenceSplitter(chunk_size=self.chunk_size_, chunk_overlap=self.overlap_)
        docs = []
        for t in tqdm(text, desc="Chunking by character length", unit="document"):
            chunks = text_splitter.split_text(t)
            docs.append(chunks)
        return docs

class SentenceChunker(BaseChunker):
    """
    A chunker that splits text based on sentence windows with overlap.
    
    This chunker creates windows of sentences that overlap, preserving
    context between chunks. Best suited for long-form text.
    """
    def __init__(self, window_size: int = 5, window_overlap: int = 1):
        """
        Initialize the chunker.

        Args:
            window_size: Number of sentences to include in each window.
            window_overlap: Number of sentences to overlap between windows.
        """
        self.window_size_ = window_size
        self.window_overlap_ = window_overlap

    def chunk(self, text: Union[str, List[str]]) -> List[List[str]]:
        """
        Split text into chunks using sentence-based window parsing.
        
        Args:
            text: The input text to be chunked. Can be a single string or a list of strings.
        
        Returns:
            A list of lists of strings, where each inner list represents chunks for a document.
        """
        if isinstance(text, str):
            text = [text]        
        
        parser = SentenceWindowNodeParser.from_defaults(
            window_size=self.window_size_,
            window_metadata_key="prev_text",
            window_overlap=self.window_overlap_,
        )
        docs = []
        for t in tqdm(text, desc="Chunking by sentence windows", unit="document"):
            chunks = parser.split_text(t)
            docs.append(chunks)
        return docs


# ==============================================================
# Semantic Chunking
# ==============================================================

class Chunks(BaseModel):
    """
    Pydantic model for structured chunk responses from the LLM.
    
    Attributes:
        chunks: A list of text chunks
    """
    chunks: List[str]

class SemanticChunker(BaseChunker):
    """
    A chunker that uses an LLM to split text based on semantic meaning.
    
    This advanced chunker uses an LLM to intelligently split text into
    semantically coherent chunks, preserving context and meaning.
    """
    def __init__(self, llm: BaseLLM) -> None:
        """
        Initialize the semantic chunker.
        
        Args:
            llm: The language model to use for semantic chunking
        """
        self.llm_: BaseLLM = llm
        self.model_: str = llm.model_args_['model']
        self.token_counter_: OpenAITokenCounter = OpenAITokenCounter(model=llm.model_args_['model'])

    def _split_text(self, text: str, max_tokens: int) -> List[str]:
        """
        Splits text into max_tokens-sized chunks without breaking words.
        
        Args:
            text: The text to split
            max_tokens: Maximum number of tokens per chunk
            
        Returns:
            A list of text chunks
        """
        encoding = tiktoken.encoding_for_model(self.model_)
        tokens = encoding.encode(text)
        
        chunks = []
        for i in tqdm(range(0, len(tokens), max_tokens), desc="Pre-splitting large text", unit="chunk"):
            end = min(i + max_tokens, len(tokens))
            chunk = encoding.decode(tokens[i:end])
            chunks.append(chunk)
        return chunks

    def chunk(self, text: Union[str, List[str]]) -> List[List[str]]:
        """
        Split text into semantically coherent chunks using an LLM.
        
        This method:
        1. Pre-splits very large text to fit within token limits
        2. Uses the LLM to split text into semantically coherent chunks
        3. Further refines chunks that are still too large
        
        Args:
            text: The input text to be chunked. Can be a single string or a list of strings.
            
        Returns:
            A list of lists of strings, where each inner list represents chunks for a document.
        """
        if isinstance(text, str):
            text = [text]  

        docs = []
        max_tokens = OPENAI_TOKEN_LIMITS[self.model_] // SAFETY_DIVISOR

        print("Semantically chunking text. This may take a while...")
        for t in tqdm(text, desc="Processing documents", unit="document"):
            # Step 1: Handle long text by splitting if needed
            if self.token_counter_.count_tokens(t) > max_tokens:
                super_blocks = self._split_text(t, max_tokens)
            else:
                super_blocks = [t]

            # Step 2: Send each chunk to OpenAI for structured chunking
            pre_chunks = []
            for block in super_blocks:
                system_prompt = SYSTEM_PROMPT
                prompt = PROMPT_BASE + f"\n\n## Original Text: {block}"
                response = self.llm_.structured_query(Chunks, prompt, system_prompt)
                pre_chunks.extend(response.chunks)

            # Step 3: Remove any chunks that are too long (second pass through LLM)
            final_chunks = []
            for chunk in pre_chunks:
                if self.token_counter_.count_tokens(chunk) > DESIRED_CHUNK_TOKENS:
                    expected_chunks = ceil(self.token_counter_.count_tokens(chunk) / DESIRED_CHUNK_TOKENS)
                    prompt = PROMPT_BASE + f"\n\n## Original Text: {chunk}\n\n## Desired Number of Chunks (if breaking does not defy Instruction # 2): {expected_chunks}"
                    response = self.llm_.structured_query(Chunks, prompt, system_prompt)
                    final_chunks.extend(response.chunks)
                else:
                    final_chunks.append(chunk)

            docs.append(final_chunks)

        return docs