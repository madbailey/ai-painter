import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from lavis.models import load_model_and_preprocess

tokenizer = AutoTokenizer.from_pretrained("TheBloke/samantha-mistral-instruct-7B-GPTQ")
model = AutoModelForCausalLM.from_pretrained("TheBloke/samantha-mistral-instruct-7B-GPTQ")