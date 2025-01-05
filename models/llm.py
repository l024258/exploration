import os
import sys

# Get the current working directory and add the parent directory to the Python path
current_working_directory = os.getcwd()
sys.path.append(os.path.join(current_working_directory, ".."))

from decouple import AutoConfig
config = AutoConfig()

class LLM:
    def __init__(self, model_name):
        self.model_name = model_name
        self.open_ai_llms_list = ['gpt-3.5', 'gpt-4', 'gpt-4o', 'gpt-4o-mini']
        self.google_llms_list = ['gemini-1.5-flash','gemini-1.5-flash-8b', 'gemini-1.5-pro']
        self.open_source_llms_list = ['mistral-chat', 'llama2-chat', 'tinyllama']
        self.gguf_llm_list = ['mistral-chat-gguf', 'llama2-chat-gguf', 'falcon2-chat-gguf']
        self.ollama_llm_list = ['llama3']

    def load_openai_model(self, deployment_name, max_tokens=8192, temp=0.0):
        os.environ["AZURE_OPENAI_API_KEY"] = config('AZURE_OPENAI_API_KEY')
        os.environ["AZURE_OPENAI_ENDPOINT"] = config('AZURE_ENDPOINT')
        from langchain_openai import AzureChatOpenAI
        llm = AzureChatOpenAI(
                openai_api_version=config('AZURE_CHAT_OPENAI_API_VERSION'),
                azure_deployment=deployment_name,
                temperature=temp,
                max_tokens=max_tokens
            )
        return llm

    def load_hf_pipeline(self, model_id, max_tokens=4096, temp=0.0, top_k=10):
        from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
        from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

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
    
    def load_llama_cpp_model(self, model_path, max_tokens=4096, temp=0.0, top_k=10):
        from langchain_community.llms import LlamaCpp

        llama_cpp = LlamaCpp(
            model_path=model_path,
            temperature=temp,
            max_tokens=max_tokens,
            top_k=top_k,
            f16_kv=True,
            n_ctx=2048
        )
        return llama_cpp
    
    def load_ollama_model(self, model_name, max_tokens=4096, temp=0.0, top_k=10):
        # Make sure to pull the model beforehand
        # ollama pull $model_name 
        from langchain_community.chat_models import ChatOllama

        llm_ollama = ChatOllama(
            model=model_name,
            temperature=temp,
            max_tokens=max_tokens,
            top_k=top_k,
        )
        return llm_ollama
    
    def load_google_model(self, model_name, max_tokens=4096, temp=0.0, top_k=10):
        os.environ["GOOGLE_API_KEY"] = config('GOOGLE_API_KEY')
        from langchain_google_genai import ChatGoogleGenerativeAI

        llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temp,
            max_tokens=max_tokens,
            timeout=None,
            max_retries=2,
            # other params...
        )
        return llm

    def load_model(self, max_tokens=4096, temp=0.0, top_k=10):
        if self.model_name in self.open_ai_llms_list:
            model2deployment = {
                # GPT-3.5 Turbo models can understand and generate natural language or code and have been optimized for chat using the Chat Completions API but work well for non-chat tasks as well.
                # Context Window: 16,385 tokens
                # Max Output Tokens: 4096 tokens
                'gpt-3.5': config('AZURE_GPT35_CHAT_OPENAI_DEPLOYMENT'),
                # GPT-4 is a large multimodal model (accepting text or image inputs and outputting text) that can solve difficult problems with greater accuracy than any of our previous models, thanks to its broader general knowledge and advanced reasoning capabilities
                # Context Window: 128,000 tokens
                # Max Output Tokens: 4096 tokens
                'gpt-4': config('AZURE_GPT4_CHAT_OPENAI_DEPLOYMENT'),
                # GPT-4o is multimodal (accepting text or image inputs and outputting text), and it has the same high intelligence as GPT-4 Turbo but is much more efficient—it generates text 2x faster and is 50% cheaper. 
                # Additionally, GPT-4o has the best vision and performance across non-English languages of any of our models.
                # Context Window: 128,000 tokens
                # Max Output Tokens: 16,384 tokens
                'gpt-4o': config('AZURE_GPT4o_CHAT_OPENAI_DEPLOYMENT'),
                # GPT-4o mini (“o” for “omni”) is our most advanced model in the small models category, and our cheapest model yet. 
                # It is multimodal (accepting text or image inputs and outputting text), has higher intelligence than gpt-3.5-turbo but is just as fast. 
                # It is meant to be used for smaller tasks, including vision tasks.
                # Context Window: 128,000 tokens
                # Max Output Tokens: 16,384 tokens
                'gpt-4o-mini': config('AZURE_GPT4o_mini_CHAT_OPENAI_DEPLOYMENT')
            }
            llm = self.load_openai_model(model2deployment[self.model_name], max_tokens, temp)
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
                'falcon2-chat-gguf' : './../models_repo/Falcon2-11B-Instruct/falcon2-11B.Q4_K_M.gguf',
            }
            llm = self.load_llama_cpp_model(name2path[self.model_name], max_tokens, temp, top_k)
        elif self.model_name in self.ollama_llm_list:
            llm = self.load_ollama_model(self.model_name, max_tokens, temp, top_k)
        elif self.model_name in self.google_llms_list:
            ## Gemini 1.5 Flash 
            ##  Gemini 1.5 Flash is a fast and versatile multimodal model for scaling across diverse tasks.
            ##  Context Window: 1,048,576 tokens
            ##  Max Output Tokens: 8,192 tokens
            ##  https://ai.google.dev/gemini-api/docs/models/gemini#gemini-1.5-flash

            ## Gemini 1.5 Flash-8B
            ##  Gemini 1.5 Flash-8B is a small model designed for lower intelligence tasks.
            ##  Context Window: 1,048,576 tokens
            ##  Max Output Tokens: 8,192 tokens
            ##  https://ai.google.dev/gemini-api/docs/models/gemini#gemini-1.5-flash-8b

            ## Gemini 1.5 Pro
            ##  Gemini 1.5 Pro is a mid-size multimodal model that is optimized for a wide-range of reasoning tasks. 1.5 Pro can process large amounts of data at once, including 2 hours of video, 19 hours of audio, codebases with 60,000 lines of code, or 2,000 pages of text.
            ##  Context Window: 2,097,152 tokens
            ##  Max Output Tokens: 8,192 tokens
            ##  https://ai.google.dev/gemini-api/docs/models/gemini#gemini-1.5-pro
            llm = self.load_google_model(self.model_name, max_tokens, temp, top_k)
        else:
            return "Model Not Found..."

        return llm