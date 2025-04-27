from src.helper import load_files, text_split, download_hugging_face_embeddings
from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv
import os
from pathlib import Path

# Load env variables
load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY

# Directories per namespace
all_data = {
    'general': "Data/general",
    'security': "Data/security",
    'monitoring': "Data/monitoring",
}

# Load embedding model
embeddings = download_hugging_face_embeddings()

# Connect to Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
index_name = "bot"

# Create index only if it doesn't exist
if index_name not in pc.list_indexes():
    print(f"[INFO] Creating index: {index_name}")
    pc.create_index(
        name=index_name,
        dimension=384,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
else:
    print(f"[INFO] Index '{index_name}' already exists. Skipping creation.")

# Helper function to batch data
def batch_data(documents, batch_size=100):
    for i in range(0, len(documents), batch_size):
        yield documents[i:i+batch_size]

# Now upload data
for namespace, data_path in all_data.items():
    print(f"[INFO] Loading: {namespace} from {data_path}")
    extracted_data = load_files(Path(data_path))
    text_chunks = text_split(extracted_data)

    print(f"[INFO] Uploading {len(text_chunks)} docs to '{index_name}' (namespace='{namespace}')")

    # Upload in batches
    for batch in batch_data(text_chunks, batch_size=100):
        PineconeVectorStore.from_documents(
            documents=batch,
            index_name=index_name,
            embedding=embeddings,
            namespace=namespace
        )

print("[INFO] ✅ Database upload complete.")
