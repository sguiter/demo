from abc import ABC, abstractmethod
import json
import os
import tempfile
import traceback
from sqlite3 import connect
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from pydantic import BaseModel
from sqlalchemy import URL

from profsandman_agents.llms import BaseLLM
from profsandman_agents.vector_databases import BaseVectorDB

# ==============================================================
# Strategy Patterns
# ==============================================================

class BaseRAGAgent(ABC):
    """
    Abstract base class for Retrieval-Augmented Generation (RAG) agents.
    
    RAG agents combine vector search with language models to provide
    context-aware responses based on a knowledge base.
    """
    @abstractmethod
    def __init__(self, llm: BaseLLM, vectordb: BaseVectorDB) -> None:
        """
        Initialize a RAG agent.
        
        Args:
            llm: The language model to use for generating responses
            vectordb: The vector database to use for retrieving context
        """
        pass
    
    @abstractmethod
    def query(self, prompt: str, k: int = 5, max_distance: float = 0.65, 
              show_citations: bool = False) -> Optional[str]:
        """
        Query the RAG agent with a prompt.
        
        Args:
            prompt: The user's question or prompt
            k: Number of documents to retrieve from the vector database
            max_distance: Maximum semantic distance threshold for retrieved documents
            show_citations: Whether to display the retrieved documents as citations
            
        Returns:
            The generated response or None if confidence is too low
        """
        pass

class BaseStructuredDataAgent(ABC):
    """
    Abstract base class for structured data agents.
    
    Structured data agents interact with databases or structured data sources
    to answer questions by generating and executing queries.
    """
    @abstractmethod
    def __init__(self, llm: BaseLLM, database_url: Union[str, URL], 
                 db_desc: Optional[str] = None, include_detail: bool = True, **kwargs) -> None:
        """
        Initialize a structured data agent.
        
        Args:
            llm: The language model to use for generating responses
            database_url: URL or path to the database
            db_desc: Optional description of the database
            include_detail: Whether to include detailed schema information
            **kwargs: Additional keyword arguments
        """
        pass
    
    @abstractmethod
    def query(self, prompt: str, view_sql: bool = False, retries: int = 0) -> Optional[str]:
        """
        Query the structured data agent with a prompt.
        
        Args:
            prompt: The user's question or prompt
            view_sql: Whether to display the generated SQL query
            retries: Number of retry attempts if the query fails
            
        Returns:
            The generated response or None if the query fails
        """
        pass
    
class BaseMultiAgent(ABC):
    """
    Abstract base class for multi-agent systems.
    
    Multi-agent systems coordinate multiple specialized agents to handle
    different types of questions or tasks.
    """
    @abstractmethod
    def __init__(self, llm: BaseLLM, 
                 agent_names: List[str],
                 agents: List[Union[BaseRAGAgent, BaseStructuredDataAgent]], 
                 agent_descriptions: List[str],
                 agent_query_kwargs: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize a multi-agent system.
        
        Args:
            llm: The language model to use for agent selection
            agent_names: Names of the available agents
            agents: List of agent instances
            agent_descriptions: Descriptions of each agent's capabilities
            agent_query_kwargs: Optional keyword arguments for each agent's query method
        """
        pass
    
    @abstractmethod
    def query(self, prompt: str, show_logic: bool = False) -> Optional[str]:
        """
        Query the multi-agent system with a prompt.
        
        Args:
            prompt: The user's question or prompt
            show_logic: Whether to display the agent selection logic
            
        Returns:
            The generated response from the selected agent
        """
        pass

# ==============================================================
# ChromaDB RAG Agent
# ==============================================================

class ChromaAgent(BaseRAGAgent):
    """
    RAG agent implementation using ChromaDB as the vector database.
    
    This agent retrieves relevant documents from a ChromaDB collection
    and uses an LLM to generate responses based on the retrieved context.
    """
    def __init__(self, llm: BaseLLM, vectordb: BaseVectorDB) -> None:
        """
        Initialize a ChromaDB RAG agent.
        
        Args:
            llm: The language model to use for generating responses
            vectordb: The ChromaDB vector database to use for retrieving context
            
        Raises:
            ValueError: If no collection is attached to the vector database
        """
        self.llm_ = llm
        self.vectordb_ = vectordb

        # Check if collection is attached
        if self.vectordb_.collection_ is None:
            raise ValueError("No collection attached to the vector database.")
        
    def query(self, prompt: str, k: int = 5, max_distance: float = 0.65, 
              show_citations: bool = False) -> Optional[str]:
        """
        Query the ChromaDB RAG agent with a prompt.
        
        Args:
            prompt: The user's question or prompt
            k: Number of documents to retrieve from the vector database
            max_distance: Maximum semantic distance threshold for retrieved documents
            show_citations: Whether to display the retrieved documents as citations
            
        Returns:
            The generated response or None if confidence is too low
            
        Note:
            Higher distance values indicate weaker matches. If the minimum
            distance exceeds max_distance, the function returns None.
        """
        # Retrieve top k results
        self.docs_, self.distances_ = self.vectordb_.retrieve(question=prompt, k=k)

        if show_citations:
            citations = [f"Citation {i+1} (Distance: {round(self.distances_[i], 2)}):\n {doc}" 
                         for i, doc in enumerate(self.docs_)]
            citations_str = "\n\n".join(citations)
            print(f"Citations:\n{citations_str}\n")

        # Check if retrieval results are below confidence threshold
        mindist = min(self.distances_)
        if mindist > max_distance:
            msg = (
                "⚠️ I'm sorry, but I don't have high confidence in answering this question. "
                "The retrieved context does not seem relevant enough.\n\n"
                f"🔹 Minimum distance found: {round(mindist, 2)} (higher values indicate weaker matches)\n"
                "🛠️ Try increasing `max_distance` or refining your query."
            )
            print(msg)
            return None

        # Construct system role and context
        system_prompt = (
            "You are an intelligent AI assistant answering a question generated from retrieval augmented generation. "
            "Use the provided context to answer "
            "the question accurately and concisely. If the context is insufficient, state that "
            "you don't have enough information rather than making assumptions.\n"
            "NEVER reference the context you received, simply use it to answer the question.\n\n"
        )

        # Format retrieved documents into context
        context_str = "\n\n".join(f"- {doc}" for doc in self.docs_)

        # Final formatted prompt
        self.prompt_ = f"{system_prompt}### Context ###\n{context_str}\n\n### Question ###\n{prompt}"

        # Query the LLM
        self.response_ = self.llm_.query(self.prompt_)
        return self.response_
    

# ==============================================================
# SQLite Structured Data Agent
# ==============================================================

class SQLResponse(BaseModel):
    """
    Pydantic model for structured SQL responses from the LLM.

    Attributes:
        sql_query: The generated SQL query
        explanation: An explanation of what the query does
    """
    sql_query: str
    explanation: str


class SQLiteAgent(BaseStructuredDataAgent):
    """
    Structured data agent for SQLite databases.

    This agent analyzes database schema, generates SQL queries based on
    natural language questions, and interprets the results.
    """
    def __init__(self, llm: BaseLLM, database_url: Union[str, URL],
                 db_desc: Optional[str] = None, include_detail: bool = True, **kwargs) -> None:
        self.llm_ = llm
        self.db_desc_ = db_desc
        self.include_detail_ = include_detail
        try:
            self.engine_ = connect(database_url, check_same_thread=False)
        except Exception as e:
            raise ValueError(f"Could not connect to database: {e}")

        self._build_schema()

    def _build_schema(self) -> None:
        schema: Dict[str, Dict[str, Any]] = {}
        itm = ['table', 'view']
        for ix in itm:
            tables = list(pd.read_sql(f"SELECT tbl_name FROM sqlite_master WHERE type = '{ix}'", self.engine_)['tbl_name'])
            if tables:
                td = {}
                for t in tables:
                    temp = pd.read_sql(f"SELECT * FROM {t} LIMIT 1", self.engine_)
                    cols = list(temp.columns)
                    types = temp.dtypes.apply(lambda x: str(x)).to_list()
                    cd = {}
                    for i, c in enumerate(cols):
                        if self.include_detail_:
                            if 'int' in types[i] or 'float' in types[i] or 'date' in types[i]:
                                unq = pd.read_sql(f"SELECT MIN([{c}]) AS mn, MAX([{c}]) AS mx FROM {t} LIMIT 1", self.engine_)
                                mn = unq['mn'].values[0]
                                mx = unq['mx'].values[0]
                                cd[c] = {'datatype': types[i], 'min': str(mn), 'max': str(mx)}
                            else:
                                unq = pd.read_sql(f"SELECT DISTINCT [{c}] AS vls FROM {t}", self.engine_)
                                cd[c] = {'datatype': types[i], 'example values': unq['vls'].to_list()[:20]}
                        else:
                            cd[c] = {'datatype': types[i]}
                    td[t] = {'columns': cd}
                schema[ix + 's'] = td
        self.schema_json_ = json.dumps(schema)

    def query(self, prompt: str, view_sql: bool = False, retries: int = 0) -> Optional[str]:
        system_prompt = (
            "You are an expert in converting real world questions into SQL queries.\n"
            "Your job is to take the question below and use the provided database architecture to convert the question into a SQLite query.\n\n"
            "You are to respond both a SQL query required to answer the provided question and a short explanation of the query.\n"
            "When you generate the SQL query, make sure to return it with proper syntax for SQLite and make it legible.\n"
            'Example Question: "I want to know every type of car that was sold"\n'
            'Example Response: "SELECT DISTINCT car_type FROM Car_Sales"\n\n'
            'Example Explanation: "The Car_Sales table has information on the total units of sales, including the brands of the car."'
        )

        if self.db_desc_ is not None:
            query = (
                "Given the following SQLite database description and architecture, please answer the following question:\n\n"
                f"Database Description:\n{self.db_desc_}\n\nDatabase Architecture:\n{self.schema_json_}\n\n"
                f"Question:\n{prompt}"
            )
        else:
            query = (
                "Given the following SQLite database architecture, please answer the following question:\n\n"
                f"Database Architecture:\n{self.schema_json_}\n\n"
                f"Question:\n{prompt}"
            )

        attempts = 0
        error_context = ""

        while attempts <= retries:
            if attempts > 0:
                retry_system_prompt = system_prompt + "\n\nYour previous SQL query failed. Please fix the issues and try again."
                retry_query = query + f"\n\nPrevious failed SQL query:\n{self.response_.sql_query}\n\nError details:\n{error_context}\n\nDatabase Architecture:\n{self.schema_json_}"
                self.response_ = self.llm_.structured_query(response_format=SQLResponse, prompt=retry_query, system_prompt=retry_system_prompt)
            else:
                self.response_ = self.llm_.structured_query(response_format=SQLResponse, prompt=query, system_prompt=system_prompt)

            if view_sql:
                print(f"ExecutedSQL:\n{self.response_.sql_query}\n\nSQL Explanation:\n{self.response_.explanation}\n")

            try:
                answer = pd.read_sql(self.response_.sql_query, self.engine_)

                if answer.empty:
                    return "The query ran successfully, but no results were found in the database."

                answer_prompt = (
                    "Given the following question, SQL query, and supporting data, "
                    "please provide a clear and concise answer to the user’s question.\n\n"
                    f"Question:\n{prompt}\n\n"
                    f"SQL Query:\n{self.response_.sql_query}\n\n"
                    f"Supporting Data:\n{answer.to_json(orient='records', indent=2)}"
                )

                summary = self.llm_.query(answer_prompt)
                return summary or "I ran the query but couldn’t summarize the results clearly."

            except Exception as e:
                error_trace = traceback.format_exc()
                error_context = f"{str(e)}\n\n{error_trace}"
                print(error_trace)
                print("The generated SQL failed to properly query the database!\n\n", self.response_.sql_query)

                if attempts >= retries:
                    return f"⚠️ SQL query failed after {retries + 1} attempt(s): {str(e)}"

            attempts += 1

        return "❌ All attempts to query the database failed."

               

# ==============================================================
# Excel Structured Data Agent
# ==============================================================

class ExcelAgent(BaseStructuredDataAgent):
    """
    Structured data agent for Excel and CSV files.
    
    This agent converts Excel/CSV files to a temporary SQLite database
    and then uses SQLiteAgent to handle queries.
    """
    def __init__(self, llm: BaseLLM, database_url: Union[str, URL], 
                 db_desc: Optional[str] = None, include_detail: bool = True, **kwargs) -> None:
        """
        Initialize an Excel agent.
        
        Args:
            llm: The language model to use for generating responses
            database_url: Path to the Excel or CSV file
            db_desc: Optional description of the data
            include_detail: Whether to include detailed schema information
            **kwargs: Additional keyword arguments
            
        Raises:
            ValueError: If the file doesn't exist or isn't an Excel/CSV file
        """
        self.llm_ = llm
        self.db_desc_ = db_desc
        self.include_detail_ = include_detail

        self._build_schema(database_url)
    
    def _build_schema(self, database_url: str) -> None:
        """
        Convert Excel/CSV file to SQLite and build schema.
        
        This method:
        1. Validates the file exists and is an Excel/CSV file
        2. Creates a temporary SQLite database
        3. Loads the Excel/CSV data into the database
        4. Transforms this instance into a SQLiteAgent
        
        Args:
            database_url: Path to the Excel or CSV file
            
        Raises:
            ValueError: If the file doesn't exist or isn't an Excel/CSV file
        """
        # Check to see if database_url is a file path
        if not os.path.exists(database_url):
            raise ValueError(f"The file path {database_url} does not exist.")

        # Verify that the file is an Excel or CSV file
        ftype = database_url[database_url.rfind('.')+1:]
        if ftype.lower() not in ['csv', 'xlsx', 'xls', 'xlsm']:
            raise ValueError(f"The file {database_url} is not an Excel or CSV file.")

        # spawn temp sqlite db
        dbpath = os.path.join(tempfile.gettempdir(), 'temp.db')
        try:
            os.remove(dbpath)
        except:
            pass

        # Create a connection to the SQLite database
        conn = connect(dbpath)

        # For each sheet in the Excel file, upload the data to the SQLite database
        def clean_table_name(name: str) -> str:
            """Clean table name to be SQLite compatible."""
            # Replace any non-alphanumeric characters (except underscores) with underscores
            import re
            cleaned = re.sub(r'[^\w\s]', '_', name)
            # Replace spaces with underscores and ensure no double underscores
            cleaned = re.sub(r'\s+', '_', cleaned)
            cleaned = re.sub(r'_+', '_', cleaned)
            # Remove leading/trailing underscores
            cleaned = cleaned.strip('_')
            return cleaned

        if 'xls' in ftype.lower():
            for sheet in pd.read_excel(database_url, sheet_name=None):
                data = pd.read_excel(database_url, sheet_name=sheet)
                table_name = clean_table_name(sheet)
                data.to_sql(table_name, conn, index=False, if_exists='replace')
        else:
            data = pd.read_csv(database_url)
            tab = database_url[database_url.rfind('\\')+1:-4]
            table_name = clean_table_name(tab)
            data.to_sql(table_name, conn, index=False, if_exists='replace')

        conn.commit()
        conn.close()     

        # Convert classes
        newmodel = SQLiteAgent(self.llm_, dbpath, db_desc=self.db_desc_, include_detail=self.include_detail_)
        self.__class__ = SQLiteAgent
        self.__dict__ = newmodel.__dict__

    def query(self, prompt: str, view_sql: bool = False, retries: int = 0) -> Optional[str]:
        """
        This method is not used as the instance is transformed into a SQLiteAgent.
        
        The actual query method used will be the one from SQLiteAgent.
        """
        pass


# ==============================================================
# Vanilla Multi-Agent
# ==============================================================

from typing import List, Dict, Optional, Union, Any
from pydantic import BaseModel

class ConductorResponse(BaseModel):
    agent_integer: int
    explanation: str

class MultiAgent(BaseMultiAgent):
    """
    Multi-agent system that selects the most appropriate agent for a given query.
    """
    def __init__(self, llm: BaseLLM, 
                 agent_names: List[str],
                 agents: List[Union[BaseRAGAgent, BaseStructuredDataAgent]], 
                 agent_descriptions: List[str],
                 agent_query_kwargs: Optional[Dict[str, Any]] = None) -> None:

        if agent_query_kwargs is None or agent_query_kwargs == {}:
            assert len(agent_names) == len(agents) == len(agent_descriptions), "All lists must be the same length"
        else:
            assert len(agent_names) == len(agents) == len(agent_descriptions) == len(agent_query_kwargs), "All lists must be the same length"

        self.llm_ = llm
        self.agent_names_ = agent_names
        self.agents_ = agents
        self.agent_descriptions_ = agent_descriptions
        self.agent_types_ = [type(agent).__name__ for agent in agents]
        self.agent_query_kwargs_ = agent_query_kwargs or [{} for _ in agent_names]

        self.system_prompt_ = (
            "You are responsible for determining the most appropriate agent for a given question "
            "based on the category descriptions. Each agent will be given a corresponding integer, "
            "and your response should include the integer of the agent that best matches the question and a short explanation.\n\n"
            "Example:\nAgent 0 (Text_Agent): Qualitative questions related to: sports history, philosophy, and rules.\n"
            "Agent 1 (Database_Agent): Quantitative/statistical questions answerable with SQL related to: sports statistics, player data.\n"
            "Question: How many points did Kobe Bryant score over his career?\nAnswer: 1\nExplanation: The question is about stats, so Agent 1 is selected."
        )

        self.prompt_ = "Use the following category descriptions to answer the following question:\n\n"
        type_tags = {
            'ChromaAgent': 'Qualitative questions related to: ',
            'SQLiteAgent': 'Quantitative questions answerable with SQL related to: ',
            'ExcelAgent': 'Spreadsheet-based questions from race data like lap times, pit stops, or summaries related to: '
        }

        for i, desc in enumerate(self.agent_descriptions_):
            final_desc = desc.strip()
            if not final_desc.endswith('.'):
                final_desc += '.'
            self.prompt_ += f"Agent {i} ({self.agent_names_[i]}):\n{type_tags.get(self.agent_types_[i], '')}{final_desc}\n"
        self.prompt_ += "\nQuestion:\n"

    def query(self, prompt: str, show_logic: bool = False) -> str:
        query_text = self.prompt_ + prompt
        response = self.llm_.structured_query(response_format=ConductorResponse, prompt=query_text, system_prompt=self.system_prompt_)

        agent_index = response.agent_integer
        explanation = response.explanation

        print(f"🧠 Agent selected: {self.agent_names_[agent_index]} ({type(self.agents_[agent_index]).__name__})")
        print(f"🤖 Reason: {explanation}")

        # 🔧 Store traceability info
        self.last_agent_ = self.agents_[agent_index]
        self.last_agent_name_ = self.agent_names_[agent_index]

        return self.agents_[agent_index].query(prompt, **self.agent_query_kwargs_[agent_index])
