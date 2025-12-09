import torch
import os
import asyncio

from typing import AsyncIterator
from typing_extensions import TypedDict
from typing import Callable
from functools import lru_cache

from transformers import TextIteratorStreamer
from transformers import BitsAndBytesConfig, AutoModelForCausalLM
# from transformers import Mistral3ForConditionalGeneration

from mistral_common.tokens.tokenizers.mistral import MistralTokenizer
from mistral_common.protocol.instruct.messages import SystemMessage, UserMessage
from mistral_common.protocol.instruct.request import ChatCompletionRequest

from threading import Thread

from huggingface_hub import login

# sys.path.insert(0, str(Path.cwd().parent / "src"))
from assurhabitat_agents.config.model_config import HF_TOKEN, LLM_BASE_MODEL, MAX_NEW_TOKENS

login(token=HF_TOKEN)

@lru_cache(maxsize=1)
def _load_model():
    
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type='nf4',
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16
        )
    
    tokenizer = MistralTokenizer.from_hf_hub(LLM_BASE_MODEL)
    model = AutoModelForCausalLM.from_pretrained(
        LLM_BASE_MODEL,
        device_map="auto",
        #torch_dtype=torch.bfloat16,
        quantization_config=bnb_config
    )
    return tokenizer, model

def llm_inference(prompt: str) -> str:
    """Réalise une inférence au LLM Devstral (nécessite du code spécifique à Mistral)."""
    tokenizer, model = _load_model()
    tokenized = tokenizer.encode_chat_completion(
        ChatCompletionRequest(
            messages=[
                UserMessage(content=prompt),
            ],
        )
    )
    output = model.generate(
        input_ids=torch.tensor([tokenized.tokens]).to("cuda"),
        max_new_tokens=MAX_NEW_TOKENS,
    )[0]
    return tokenizer.decode(output[len(tokenized.tokens):])