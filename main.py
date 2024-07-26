import os
import re
import streamlit as st
from dotenv import load_dotenv
from langchain_community.llms import Ollama
from langchain import PromptTemplate
from langchain.chains import RetrievalQA
from redis import Redis
from langchain.vectorstores.redis import Redis
import time
from redis import Redis as RedisClient
from preprocess import process_latex_file, textSplitter_latex, SentenceTransformerEmbeddings

# Load environment variables
load_dotenv()
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")

## loading and preprocessing
file_path = "Probability/01.zip"
data = process_latex_file(file_path)

llm=Ollama(model="qwen2")
embeddings_model_name = 'Alibaba-NLP/gte-base-en-v1.5'
embeddings_model = SentenceTransformerEmbeddings(embeddings_model_name)
vectordb_file_path = 'Redis'

# Redis connection details
redis_url = "redis://localhost:6379" 
index_name = "base" 

def create_vector_db(file_path,chunk_size=1000,chunk_overlap=50):
    #Load data
    data = process_latex_file(file_path)
    
    # Split data into LangChain Document objects
    chunks = textSplitter_latex(data, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    # Connect to Redis
    redis_client = RedisClient.from_url(redis_url)

    # Flush the existing data
    redis_client.flushdb()
    
    # Redis vector store
    rds = Redis.from_documents(
        chunks,
        embeddings_model,
        redis_url= redis_url,
        index_name="users",
    )
    rds.write_schema(vectordb_file_path)

def get_qa_chain(k=3):

    new_rds = Redis.from_existing_index(
        embeddings_model,
        index_name="users",
        redis_url= redis_url,
        schema= vectordb_file_path,
    )
    
    retriever = new_rds.as_retriever(search_type="similarity", search_kwargs={"k": k})
    
    prompt_template = """
    You are a QA bot designed to answer queries using TeX documents. Your goal is to generate an answer based on this context only.
    Ensure your responses meet the following criteria:
    1. Mathematical Accuracy: If the query involves a math problem, solve it independently to fully understand the query. 
    Then verify if the necessary information is available in the context.
    Compare your solution with the context to ensure consistency and accuracy, and then respond appropriately.
    2. Citation: Provide accurate citations for all information and formulas used.
    3. Content Utilization: If the query is not a math problem, make sure most of the text in the output is from the CONTEXT without making many changes.
    If the answer is not found in the context, kindly state "I don't know." Don't try to make up an answer.
    CONTEXT: {context}

    QUERY: {question}
    """

    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )
    chain = RetrievalQA.from_chain_type(llm=llm,
                                        chain_type="stuff",
                                        retriever=retriever,
                                        input_key="query",
                                        return_source_documents=True,
                                        chain_type_kwargs={"prompt": PROMPT})

    return chain

def clean_output(output):
    out_modified = re.sub(r"\n", r"\n ", output)
    out_modified = re.sub(r"(?<!\$)\\$(?!\$)", r"\$ \n ", out_modified)
    out_modified = re.sub(r"\$\$", r"\n $$ \n ", out_modified)
    out_modified = re.sub(r"\\\\text", r"\\text", out_modified)
    return out_modified

# Function to run the chain and parse the output
def run_chain_with_parser(chain, query):
    result = chain({"query": query})

    out_modified = clean_output(result['result'])
    source_doc = [clean_output(doc_s.page_content) for doc_s in result["source_documents"]]
    
    return {
        "output" : out_modified,
        "source_documents": source_doc    
    }

def run(k=3):
    st.title("Math Q&A 🌱 qwen2")
    query = st.text_input("Question: ")

    if query:
        chain = get_qa_chain(k=k)
        output = run_chain_with_parser(chain, query)    

        st.header("Answer")
        st.markdown(output['output'])
        
if __name__ == "__main__":
    create_vector_db(file_path, chunk_size=500,chunk_overlap=100)    
    run(k=5)
