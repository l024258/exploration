import json
import os
from sentence_transformers import SentenceTransformer, util
import time
import gzip
import os
import torch
import sys
import pandas as pd
import numpy as np
from transformers import pipeline
import csv

#python retrieval_qa_druglabeling_batch.py  
# We use the Bi-Encoder to encode all passages, so that we can use it with sematic search
#model_name = 'nq-distilbert-base-v1'
# model_name = 'msmarco-distilbert-base-v3'
#model_name = 'msmarco-roberta-base-v3'
#model_name = 'msmarco-roberta-base-ance-fristp'

model_name = 'multi-qa-mpnet-base-dot-v1'
bi_encoder = SentenceTransformer(model_name)
top_k = 1
passages = []


file_name = 'clinicalTrials_sample_dataset.txt'
passages = open(file_name).readlines()
passages = [par.strip() for par in passages]
print("Number of Passages:", len(passages))

# To speed things up, pre-computed embeddings are downloaded.
# The provided file encoded the passages with the model 'nq-distilbert-base-v1'
if model_name == 'nq-distilbert-base-v1':
    embeddings_filepath = 'simplewiki-2020-11-01-nq-distilbert-base-v1.pt'
    if not os.path.exists(embeddings_filepath):
        util.http_get('http://sbert.net/datasets/simplewiki-2020-11-01-nq-distilbert-base-v1.pt', embeddings_filepath)

    corpus_embeddings = torch.load(embeddings_filepath)
    corpus_embeddings = corpus_embeddings.float()  # Convert embedding file to float
    if torch.cuda.is_available():
        corpus_embeddings = corpus_embeddings.to('cuda')
else:  # Here, we compute the corpus_embeddings from scratch (which can take a while depending on the GPU)
    corpus_embeddings = bi_encoder.encode(passages, convert_to_tensor=True, show_progress_bar=True)

print ("Initiating QA engine ...")

qa_nlp = pipeline("question-answering", model='dmis-lab/biobert-large-cased-v1.1-squad')
t2tg_nlp = pipeline("text2text-generation", model='google/flan-t5-base')

questions = ["What drug is currently approved by FDA for the treatment of autoimmune disorders?",
             "What does the SARS-CoV-2 spike protein contains?",
             "How many subjects will be enrolled in Arm B?",
             "Does Phase I study evaluates Safety, Tolerability, and Immunogenicity of a PIKA COVID-19 Vaccine in Healthy Individuals?"]

print ("starting processing questions ...\n")
for que in questions:
    #query = input("Please enter a question: ")
    query = que.strip()
    # Encode the query using the bi-encoder and find potentially relevant passages
    start_time = time.time()
    question_embedding = bi_encoder.encode(query, convert_to_tensor=True)
    hits = util.semantic_search(question_embedding, corpus_embeddings, top_k=top_k)
    hits = hits[0]  # Get the hits for the first query
    end_time = time.time()
    
    answers = [] 
    print("Question  ::  ", query)
    for i, hit in enumerate(hits):
        print("Passage {} ::  {}\nConfidence  ::  {}".format(i+1, passages[hit['corpus_id']], hit['score']))
        context = passages[hit['corpus_id']]
        
        results = qa_nlp(question=query, context=context)
        print("QA Answer :: {} ---------- {}".format(results["answer"], results["score"]))
        answers.append((results["score"], results["start"], results["end"], results["answer"], context))

        results = t2tg_nlp("Question: "+query+" Context: "+context)
        print("T2TG Answer :: {}".format(results))
    print()
