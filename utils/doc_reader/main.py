from utils.doc_reader.pdf import PyPDFLoader
from utils.doc_reader.word_document import Docx2txtLoader
from langchain_community.document_loaders import TextLoader

def file_parser(filename, tool_name=None):
    if filename.split('.')[-1] == 'pdf':
        loader = PyPDFLoader(filename)
        pages = loader.load_and_split()
    elif filename.split('.')[-1] in ['docx', 'doc']:
        loader = Docx2txtLoader(filename)
        pages = loader.load_and_split()
    elif filename.split('.')[-1] in ['txt']:
        loader = TextLoader(filename)
        pages = loader.load()
    
    return pages