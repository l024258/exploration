from langchain_openai import AzureOpenAIEmbeddings
from langchain.embeddings import HuggingFaceEmbeddings
import torch

from decouple import AutoConfig
config = AutoConfig(search_path='./../.env')

class EM:
    def __init__(self, model_name):
        self.model_name = model_name
        self.open_source_llms_list = ['e5-base']

    def load_model(self):
        if self.model_name == 'ada-2':
            embeddings = AzureOpenAIEmbeddings(
                azure_deployment=config('AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT_NAME'),
                openai_api_version=config('AZURE_OPENAI_EMBEDDINGS_API_VERSION'),
                chunk_size=1
            )
        if self.model_name in self.open_source_llms_list:
            name2id = {
                'e5-base': "intfloat/e5-base-v2",
            }
            model_kwargs = {'device': 'cuda' if torch.cuda.is_available() else 'cpu'}
            encode_kwargs = {'normalize_embeddings': True}
            
            embeddings = HuggingFaceEmbeddings(
                model_name=name2id[self.model_name],
                model_kwargs=model_kwargs,
                encode_kwargs=encode_kwargs
            )
        return embeddings