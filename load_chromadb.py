import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from profsandman_agents.text_extractors import BaseTextExtractor
from profsandman_agents.chunkers import SemanticChunker
from profsandman_agents.embedders import SentenceTransformerEmbedder
from profsandman_agents.vector_databases import ChromaDBVectorDB
from profsandman_agents.llms import OpenAILLM

# Create our own simple extractor with filenames for traceability
class SimpleTextExtractor(BaseTextExtractor):
    def extract(self, file_paths):
        docs = []
        
        # Define the number of threads for concurrent file reading
        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(self.read_file, path): path for path in file_paths}
            for future in as_completed(futures):
                doc = future.result()  # Get the result from the future
                if doc:  # If doc is not None, append it
                    docs.append(doc)
        return docs

    # Helper method to read a single file (to be used in the ThreadPoolExecutor)
    def read_file(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return {
                    "text": f.read(),
                    "metadata": {"source": os.path.basename(path)}  # ✅ Step 1: Add filename as metadata
                }
        except Exception as e:
            print(f"Error reading {path}: {e}")
            return None

# Setup
api_key = open(r"C:\Users\gwapi\OneDrive - Marquette University\AIM\AIM 4420\OPENAI_KEY.txt").read()
llm = OpenAILLM(api_key=api_key)

# Setup components
embedder = SentenceTransformerEmbedder()
text_extractor = SimpleTextExtractor()
chunker = SemanticChunker(llm)

vdb = ChromaDBVectorDB(
    dbpath="10K Docs",  # ✅ Use forward slashes or raw strings
    embedder=embedder,
    distance_measure="cosine",
    text_extractor=text_extractor,
    chunker=chunker
)

vdb.initialize_db()
vdb.initialize_collection("semanticchunker_db")

# Load all .txt files
folder_path = "10K Docs"
file_paths = [
    os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(".txt")
]

# Add documents
vdb.add_to_collection(file_paths)
print("✅ Documents loaded successfully with traceability!")
