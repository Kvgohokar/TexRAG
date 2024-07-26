# TexRAG: A Tex File-Based RAG Bot with Open Source Modules

TexRAG is a project aimed at implementing a Retrieval-Augmented Generation (RAG) bot specifically designed to process and answer questions based on TeX files. 

## LaTeX Parser
LATEX (pronounced “LAY-tek” or “LAH-tek”) is a tool for typesetting, commonly used for technical and scientific documentation. It provides control over document structure and formatting, making it a preferred choice for producing complex documents such as research papers, theses, and technical reports.

TexRAG includes a custom LaTeX parser that converts LaTeX documents into structured JSON objects. This allows for efficient extraction and processing of text, formulas, image captions from TeX files.

## Open Source RAG with LangChain and Ollama

The two key open-source projects used in this project are LangChain and Ollama. LangChain is a versatile framework that simplifies the creation of applications using large language models (LLMs). Ollama complements this by providing a powerful, user-friendly platform for running LLMs locally. 

## RAG Pipeline
Retrieval Augmented Generation (RAG) is a technique for augmenting LLM knowledge with additional data from an external knowledge source. This allows generation of more accurate and contextual answers while reducing hallucinations.

The RAG pipeline includes the following steps:
1. **Preprocessing**: The LaTeX document is parsed and converted into JSON format.
2. **Chunking**: The document is divided into smaller, manageable chunks using a custom chunking strategy.
3. **Embedding**: Each chunk is embedded using sentence transformer models.
4. **Storage**: Embedded chunks are stored in a Redis vector store.
5. **Prompt template**: Used to guide the language model in generating relevant and contextually accurate responses.
5. **Retrieval**: Relevant chunks are retrieved based on the query.
6. **Generation**: Retrieved chunks are used to generate the final answer using the Qwen2 model.

### Testing
Manual testing was conducted using a collection of queries derived from .tex files, with the primary evaluation criteria being mathematical accuracy and the extraction of relevant information.
