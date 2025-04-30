from abc import ABC, abstractmethod
from enum import Enum
import os
from typing import List, Optional, Tuple, Union
from uuid import uuid4

import chromadb

from profsandman_agents.chunkers import BaseChunker
from profsandman_agents.embedders import BaseEmbedder
from profsandman_agents.text_extractors import BaseTextExtractor

# ==============================================================
# Strategy Pattern
# ==============================================================

class BaseVectorDB(ABC):
    """
    Abstract base class for vector database implementations used in retrieval augmented generation.
    
    This class defines the interface for vector database operations including creation, connection,
    collection management, document ingestion, and similarity search retrieval.
    """
    @abstractmethod
    def __init__(self, 
                 dbpath: str,
                 embedder: BaseEmbedder,
                 text_extractor: Optional[BaseTextExtractor] = None,
                 chunker: Optional[BaseChunker] = None,  
                 distance_measure: Optional[str] = None) -> None:
        """
        Initialize the vector database with a chunker and embedder.

        Args:
            dbpath: Path where the vector database should be created  
            embedder: Embedding strategy for document processing
            text_extractor: Text extraction strategy for document processing
            chunker: Chunking strategy for document processing
            distance_measure: Distance metric for similarity calculations
        """
        pass

    @abstractmethod
    def initialize_db(self) -> None:
        """
        Create a new database at the specified path if it doesn't exist,
        or attach to an existing one if it does.
        """
        pass
    
    @abstractmethod
    def initialize_collection(self, collection_name: str) -> None:
        """
        Creates a new or attaches to an existing collection in the database.

        Args:
            collection_name: Name of the collection to create or attach to
        """
        pass
    
    @abstractmethod
    def add_to_collection(self, file_paths: Union[str, List[str]]) -> None:
        """
        Process and add documents to a collection in the vector database.

        Args:
            file_paths: Path or list of paths to documents to process
        """
        pass

    @abstractmethod
    def retrieve(self, question: str, k: int = 5) -> Tuple[List[str], List[float]]:
        """
        Retrieve the k most relevant text chunks for a given query.

        Args:
            question: Query text to find relevant chunks for
            k: Number of chunks to retrieve. Defaults to 5.

        Returns:
            Tuple containing:
            - List of k most relevant text chunks
            - List of corresponding similarity distances
        """
        pass
    
    
# ==============================================================
# ChromaDB
# ==============================================================

class ChromaDistanceMeasure(Enum):
    """
    Enum for ChromaDB distance measures.
    
    Attributes:
        COSINE: Cosine similarity (1 - cosine similarity)
        EUCLIDEAN: Euclidean distance
        IP: Inner product (1 - inner product)
    """
    COSINE = "cosine"
    EUCLIDEAN = "euclidean"
    IP = "ip"

class ChromaDBVectorDB(BaseVectorDB):
    """
    ChromaDB implementation of BaseVectorDB for Retrieval-Augmented Generation (RAG).
    
    This class provides methods to create and manage a ChromaDB vector database,
    add documents to collections, and retrieve relevant documents based on queries.
    """

    def __init__(self, 
                 dbpath: str,
                 embedder: BaseEmbedder,
                 text_extractor: Optional[BaseTextExtractor] = None,
                 chunker: Optional[BaseChunker] = None,  
                 distance_measure: Optional[str] = ChromaDistanceMeasure.COSINE.value) -> None:
        """
        Initialize ChromaDB with a chunker and embedder.
        
        Args:
            dbpath: Path where the ChromaDB database should be created
            embedder: Embedding strategy for document processing
            text_extractor: Text extraction strategy for document processing
            chunker: Chunking strategy for document processing
            distance_measure: Distance metric for similarity calculations
            
        Note:
            If text_extractor, chunker, or distance_measure is None, the database
            will be in retrieval-only mode and cannot add new documents.
        """
        # Minimum required arguments
        self.dbpath_: str = dbpath
        self.embedder_: BaseEmbedder = embedder

        # Optional arguments
        self.chunker_: Optional[BaseChunker] = chunker
        self.text_extractor_: Optional[BaseTextExtractor] = text_extractor
        self.distance_measure_: str = distance_measure

        # Check if the vector database is retrieval only
        self.retrieval_only_: bool = False
        if self.text_extractor_ is None or self.chunker_ is None or self.distance_measure_ is None:
            self.retrieval_only_ = True
            print("WARNING: Without specifying a text extractor, chunker, and distance measure, the vector database can only be used for retrieval.")

        # Initialize client and collection
        self.client_ = None
        self.collection_ = None

    def initialize_db(self) -> None:
        """
        Create a new ChromaDB database at the specified path if it doesn't exist,
        or attach to an existing one if it does.
        
        This method creates the directory for the database if it doesn't exist
        and initializes a PersistentClient connection.
        """
        if not os.path.exists(self.dbpath_):
            os.makedirs(self.dbpath_)
            print(f"Created new database directory at {self.dbpath_}")
        self.client_ = chromadb.PersistentClient(path=self.dbpath_)

    def initialize_collection(self, collection_name: str) -> None:
        """
        Creates a new or attaches to an existing collection in ChromaDB with a specified distance metric.

        Args:
            collection_name: Name of the collection to create or attach to

        Raises:
            ValueError: If the database is not initialized
            
        Note:
            It's recommended to use the ChromaDistanceMeasure enum for the distance measure.
            Example: collection_name = ChromaDistanceMeasure.COSINE.value
        """
        if not self.client_:
            raise ValueError("Database is not initialized. Call initialize_db first.")
        
        if ' ' in collection_name:
            raise ValueError("Collection name cannot contain spaces.")

        self.collection_ = self.client_.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": self.distance_measure_}
        )

    def add_to_collection(self, file_paths: Union[str, List[str]]) -> None:
        """
        Chunk and embed documents, then store them in the vector database.
        
        This method:
        1. Extracts text from the provided file paths
        2. Chunks the extracted text
        3. Embeds each chunk
        4. Adds the chunks and embeddings to the collection
        
        Args:
            file_paths: Path or list of paths to documents to process
            
        Raises:
            ValueError: If the database is in retrieval-only mode or no collection is selected
        """
        if self.retrieval_only_:
            raise ValueError("Vector database is in retrieval only mode. Cannot add documents without text_extractor, chunker, and distance_measure.")

        if not self.collection_:
            raise ValueError("No collection selected. Call initialize_collection first.")

        if isinstance(file_paths, str):
            file_paths = [file_paths]

        # Extract text from documents
        if self.text_extractor_ is not None:
            documents = self.text_extractor_.extract(file_paths)
        else:
            raise ValueError("No text extractor provided. Cannot extract text from documents.")

        if isinstance(documents, str):
            documents = [documents]

        for i, document in enumerate(documents):
            # Chunk the document
            print(f"Beginning chunking of document {i+1})")
            chunks = self.chunker_.chunk(document)[0]

            # Embed the chunks
            chunk_embeddings = self.embedder_.embed(chunks)[0]
            
            print("Chunk Length: ", len(chunks))
            print("Chunk Embedding Length: ", len(chunk_embeddings))

            # Add each chunk and its embedding to the collection
            print(f"Beginning embedding of chunks for document {i+1}")
            for idx, (chunk, embedding) in enumerate(zip(chunks, chunk_embeddings)):
                self.collection_.add(
                    ids=[str(uuid4())],
                    embeddings=[embedding],
                    documents=[chunk]
                )

    def retrieve(self, question: str, k: int = 5) -> Tuple[List[str], List[float]]:
        """
        Retrieve the k most relevant text chunks for a given query.
        
        This method:
        1. Embeds the query using the embedder
        2. Performs a similarity search in the collection
        3. Returns the most relevant documents and their distances
        
        Args:
            question: Query text to find relevant chunks for
            k: Number of chunks to retrieve
            
        Returns:
            Tuple containing:
            - List of k most relevant text chunks
            - List of corresponding similarity distances
            
        Raises:
            ValueError: If no collection is selected
        """
        if not self.collection_:
            raise ValueError("No collection selected. Call initialize_collection first.")

        # Embed the query
        query_embedding = self.embedder_.embed(question)[0][0]

        # Perform similarity search
        results = self.collection_.query(
            query_embeddings=[query_embedding],
            n_results=k
        )

        return results["documents"][0], results["distances"][0]