import torch
import os
import asyncio

from typing import AsyncIterator
from typing_extensions import TypedDict
from typing import Callable

from transformers import TextIteratorStreamer
from transformers import BitsAndBytesConfig, AutoModelForCausalLM
from transformers import Mistral3ForConditionalGeneration

from mistral_common.tokens.tokenizers.mistral import MistralTokenizer
from mistral_common.protocol.instruct.messages import SystemMessage, UserMessage
from mistral_common.protocol.instruct.request import ChatCompletionRequest

from threading import Thread

from huggingface_hub import login

# sys.path.insert(0, str(Path.cwd().parent / "src"))
from assurhabitat_agents.config.config import HF_TOKEN, BASE_MODEL, MAX_NEW_TOKENS

login(token=HF_TOKEN)

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type='nf4',
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.bfloat16
)

tokenizer = MistralTokenizer.from_hf_hub(BASE_MODEL)
model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    quantization_config=bnb_config,
    device_map="auto"
)

def llm_inference(prompt: str) -> str:
    """Réalise une inférence au LLM Devstral (nécessite du code spécifique à Mistral)."""
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

async def llm_stream(prompt: str) -> AsyncIterator[str]:
    """Générateur asynchrone qui streame les tokens de Devstral."""
    # Tokenize input
    tokenized = tokenizer.encode_chat_completion(
        ChatCompletionRequest(messages=[UserMessage(content=prompt)])
    )

    input_ids = torch.tensor([tokenized.tokens]).to(model.device)

    # Create streamer
    streamer = TextIteratorStreamer(tokenizer, skip_prompt=True)

    # Generate in a separate thread (required for streamer)
    def generate():
        model.generate(
            input_ids=input_ids,
            max_new_tokens=4096,
            streamer=streamer,
        )

    thread = Thread(target=generate)
    thread.start()

    # Iterate over streamer outputs asynchronously
    loop = asyncio.get_event_loop()
    for token_text in streamer:
        # Allow async iteration
        yield token_text