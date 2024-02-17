from langchain_community.vectorstores import Chroma
from langchain.docstore.document import Document
from langchain.vectorstores.base import VectorStoreRetriever
import os

class VectorDB:
    def __init__(self):
        pass
    
    def create_and_dump(self, embedding_model, text_splitter, inp_text, metadata=[]):
        if isinstance(inp_text, str):
            texts = text_splitter.split_text(inp_text)
            if metadata:
                docs = [Document(page_content=t.strip(), metadata=metadata) for t in texts]
            else:
                docs = [Document(page_content=t.strip()) for t in texts]
        else:
            docs = text_splitter.split_documents(inp_text)
        if not os.path.exists('./../temp'):
            os.mkdir('./../temp')
        vectorstore = Chroma.from_documents(docs, embedding_model, persist_directory='./../temp/chroma_db')

        return vectorstore

    def load_retriever(self, embedding_function, vectorstore_path='./../temp/chroma_db'):
        vectorstore = Chroma(persist_directory=vectorstore_path, embedding_function=embedding_function)
        retriever = VectorStoreRetriever(vectorstore=vectorstore)
        return retriever
