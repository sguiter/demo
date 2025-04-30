from profsandman_agents.embedders import SentenceTransformerEmbedder
from profsandman_agents.llms import OpenAILLM
from profsandman_agents.vector_databases import ChromaDBVectorDB
from profsandman_agents.agents import MultiAgent, ChromaAgent, SQLiteAgent, ExcelAgent

# Load API key
with open(r"C:\Users\gwapi\OneDrive - Marquette University\AIM\AIM 4420\OPENAI_KEY.txt", "r") as f:
    api_key = f.read()

llm = OpenAILLM(api_key=api_key)

embedder = SentenceTransformerEmbedder()
vdb = ChromaDBVectorDB(
    dbpath="10K Docs",
    embedder=embedder,
    distance_measure="cosine"
)
vdb.initialize_db()
vdb.initialize_collection("semanticchunker_db")

# Optional: Print document count
try:
    collection = vdb.collection_
    if collection:
        print(f"🔍 ChromaDB contains {collection.count()} documents.")
    else:
        print("⚠️ No collection initialized.")
except Exception as e:
    print(f"⚠️ Error checking ChromaDB documents: {e}")

rag_agent = ChromaAgent(llm, vdb)
rag_kwargs = {"k": 15, "max_distance": 0.95, "show_citations": True}


multi_agent = MultiAgent(
    llm,
    agent_names=["Rag Agent"],
    agents=[rag_agent],
    agent_descriptions=[
        "Act as an Expert publicly traded equities in the United States."
    ],
    agent_query_kwargs=[rag_kwargs]
)

def query_race_agent(user_input):
    try:
        response = multi_agent.query(user_input)

        # print(f"RESPONSE: {response}")

        agent_used = getattr(multi_agent, "last_agent_name_", "Unknown")

        # print(f"AGENT USED: {agent_used}")

        agent_type = type(getattr(multi_agent, "last_agent_", None)).__name__

        # print(f"AGENT TYPE: {agent_type}")

        trace = "Trace not available."

        if agent_type == "ChromaAgent":
            trace = "\n\n".join(getattr(multi_agent.last_agent_, "docs_", []))

        formatted_trace = f"🔎 **Agent Used:** {agent_used}\n\n{trace}"

        # print(f"TRACE: {formatted_trace}")

        return response, formatted_trace

    except Exception as e:
        return "An error occurred while querying the chatbot.", f"❌ Error: {str(e)}"
