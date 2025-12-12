import os
from dotenv import load_dotenv
from huggingface_hub import login

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
login(token=HF_TOKEN, add_to_git_credential=False)

LLM_BASE_MODEL = "mistralai/Devstral-Small-2507"
#VLM_BASE_MODEL = "meta-llama/Llama-3.2-11B-Vision-Instruct"
VLM_BASE_MODEL = "Qwen/Qwen2-VL-2B-Instruct"

MAX_NEW_TOKENS = 4096

N_HISTORY_ENTRIES = 10