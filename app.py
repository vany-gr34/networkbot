from flask import Flask, render_template, jsonify, request
from src.helper import download_hugging_face_embeddings
from langchain_pinecone import PineconeVectorStore
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from src.prompt import *
import os

app = Flask(__name__)

load_dotenv()

# Configuration
PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
GROQ_API_KEY = os.environ.get('groq_key')
INDEX_NAME = "bot"

os.environ.update({
    "PINECONE_API_KEY": PINECONE_API_KEY,
    "groq_key": GROQ_API_KEY
})

embeddings = download_hugging_face_embeddings()
llm = ChatGroq(api_key=GROQ_API_KEY, model="llama3-70b-8192")

# Initialize all expert chains
expert_chains = {
    expert: create_retrieval_chain(
        PineconeVectorStore.from_existing_index(
            index_name=INDEX_NAME,
            embedding=embeddings,
            namespace=expert
        ).as_retriever(
            search_type="similarity_score_threshold", 
            search_kwargs={"score_threshold": 0.75, "k": 3}),
        create_stuff_documents_chain(
            llm,
            ChatPromptTemplate.from_messages([
                ("system", chatbot_prompts[expert]),
               ("human", "Context:\n{context}\n\nQuestion:\n{input}")
            ])
        )
    )
    for expert in ['general', 'security', 'monitoring']
}

@app.route("/")
def index():
    return render_template('chat.html', experts=list(expert_chains.keys()))

@app.route("/get", methods=["POST"])
@app.route("/get", methods=["POST"])
def chat():
    data = request.get_json()
    msg = data.get("msg")
    expert = data.get("expert", "general")  # Default to general if not specified
    
    if expert not in expert_chains:
        return jsonify({"error": "Invalid expert specified"}), 400
    
    
    response = expert_chains[expert].invoke({"input": msg})
    greetings = ["hi", "hello", "hey", "bonjour", "salut", "hola", "yo", "good morning", "good evening"]
    if msg.lower().strip() in greetings:
        return jsonify({
            "answer": "Hello! How can I help you today?",
            "expert_used": expert
        })

    # Check if no context (empty list)
    if not response.get("context"):
        return jsonify({
            "answer": "I could not find relevant information in the provided documents.",
            "expert_used": expert
        })

    #  Let's log the used documents:
    context_docs = response["context"]  # This is a list of documents
    for idx, doc in enumerate(context_docs):
        print(f"\n--- Context Document {idx+1} ---")
        print(doc.page_content)
        print("--------------------------\n")

    return jsonify({
        "answer": response["answer"],
        "expert_used": expert
    })

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)