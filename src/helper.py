from langchain.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from pathlib import Path




def load_files(directory):
    documents = []
    for file_path in directory.glob("**/*"):
        try:
            if file_path.suffix == ".pdf":
                loader = PyPDFLoader(str(file_path))
            elif file_path.suffix == ".txt":
                loader = TextLoader(str(file_path), encoding='utf-8')
            else:
                continue  # Skip unknown file types

            docs = loader.load()
            documents.extend(docs)

        except Exception as e:
            print(f"[WARNING] Skipping file {file_path.name}: {e}")

    return documents




#Split the Data into Text Chunks
def text_split(extracted_data):
    text_splitter=RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=20)
    text_chunks=text_splitter.split_documents(extracted_data)
    return text_chunks



#Download the Embeddings from HuggingFace 
def download_hugging_face_embeddings():
    embeddings=HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')  #this model return 384 dimensions
    return embeddings


        
