from langchain_openai import AzureChatOpenAI, AzureOpenAI
from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from langchain_community.llms import LlamaCpp

from decouple import AutoConfig
config = AutoConfig(search_path='./../.env')

class LLM:
    def __init__(self, model_name):
        self.model_name = model_name
        self.open_source_llms_list = ['mistral-chat', 'llama2-chat', 'tinyllama']
        self.gguf_llm_list = ['mistral-chat-gguf', 'llama2-chat-gguf']

    def load_hf_pipeline(self, model_id, max_tokens=256, temp=0.0, top_k=10):
        model_id = model_id
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        model = AutoModelForCausalLM.from_pretrained(model_id)
        pipe = pipeline("text-generation", 
                        model=model, 
                        tokenizer=tokenizer,
                        pad_token_id=tokenizer.eos_token_id,
                        model_kwargs={"temperature": temp, "top_k": top_k},
                        max_new_tokens=max_tokens,
                        trust_remote_code=True, 
                        device_map="auto",
               )
        hf = HuggingFacePipeline(pipeline=pipe)

        return hf
    
    def load_llama_cpp_model(self, model_path, max_tokens=256, temp=0.0, top_k=10):
        llama_cpp = LlamaCpp(
            model_path=model_path,
            temperature=temp,
            max_tokens=max_tokens,
            top_k=top_k,
            f16_kv=True,
             n_ctx=2048
        )
        return llama_cpp

    def load_model(self, max_tokens=256, temp=0.0, top_k=10):
        if self.model_name == 'gpt-3':
            llm = AzureOpenAI(
                deployment_name=config('AZURE_OPENAI_DEPLOYMENT_NAME'),
                model_name=config('AZURE_OPENAI_MODEL_NAME'),
                api_version = config('AZURE_OPENAI_API_VERSION'),
                temperature=temp,
                max_tokens=max_tokens
            )
        elif self.model_name == 'gpt-4':
            llm = AzureChatOpenAI(
                openai_api_version=config('AZURE_CHAT_OPENAI_API_VERSION'),
                azure_deployment=config('AZURE_CHAT_OPENAI_DEPLOYMENT'),
                temperature=temp,
                max_tokens=max_tokens
            )
        elif self.model_name in self.open_source_llms_list:
            name2id = {
                'mistral-chat' : "mistralai/Mistral-7B-Instruct-v0.2",
                'llama2-chat' : "meta-llama/Llama-2-7b-chat-hf",
                'tinyllama' : "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
            }
            llm = self.load_hf_pipeline(name2id[self.model_name], max_tokens, temp, top_k)
        elif self.model_name in self.gguf_llm_list:
            name2path = {
                'mistral-chat-gguf' : "./../models_repo/Mistral-7B-Instruct/mistral-7b-instruct-v0.2.Q4_K_M.gguf",
                'llama2-chat-gguf' : "./../models_repo/Llama2-7B-chat/llama-2-7b-chat.Q4_K_M.gguf",
            }
            llm = self.load_llama_cpp_model(name2path[self.model_name], max_tokens, temp, top_k)
        else:
            return "Model Not Found..."

        return llm