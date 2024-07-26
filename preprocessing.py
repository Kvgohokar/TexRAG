import zipfile
import json
from Latex_Parser import create_json_object

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_text_splitters import (
    Language,
    RecursiveCharacterTextSplitter,
)

from langchain.embeddings.base import Embeddings
from sentence_transformers import SentenceTransformer
from typing import List

def process_latex_file(file_path):
    latex_code = ""
    
    if zipfile.is_zipfile(file_path):
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            for file_name in zip_ref.namelist():
                if file_name.endswith('.tex'):
                    with zip_ref.open(file_name) as tex_file:
                        latex_code = tex_file.read().decode('utf-8')
                    break
    else:
        with open(file_path, 'r', encoding='utf-8') as tex_file:
            latex_code = tex_file.read()

    # Preprocess the LaTeX code and create the JSON object
    json_object = create_json_object(latex_code)
    
    return json_object


def textSplitter_latex(data, chunk_size=1000, chunk_overlap=50):
    latex_splitter = RecursiveCharacterTextSplitter.from_language(
        language=Language.MARKDOWN, chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    latex_data = json.dumps(data["Content"], indent=4)
    latex_docs = latex_splitter.create_documents([latex_data])

    text_splitter = RecursiveCharacterTextSplitter(
        separators=[',\n  ', ',\\n  '], 
        chunk_size=10,
        chunk_overlap=0,
        length_function=len,
        is_separator_regex=False,
    )

    equations_data = json.dumps(data["Equations"])
    equations = text_splitter.create_documents([equations_data])

    table_data = json.dumps(data["Tables"], indent=4)
    tables = text_splitter.create_documents([table_data])

    image_captions_data = json.dumps(data["Image Captions"], indent=4)
    captions = text_splitter.create_documents([image_captions_data])

    title_data = json.dumps(data["Title"], indent=4)
    title = text_splitter.create_documents(["title " + title_data])

    author_data = json.dumps(data["Author"], indent=4)
    author = text_splitter.create_documents(["author " + author_data])

    date_data = json.dumps(data["Date"], indent=4)
    date = text_splitter.create_documents(["date " + date_data])

    chunks = latex_docs + equations + tables + captions + title + author + date
    return chunks


class SentenceTransformerEmbeddings(Embeddings):
    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name, trust_remote_code=True)

    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        return self.model.encode(documents)

    def embed_query(self, query: str) -> List[float]:
        return self.model.encode([query])[0]

