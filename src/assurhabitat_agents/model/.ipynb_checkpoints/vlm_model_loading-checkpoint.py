#src/assurhabitat_agents/model/vlm_model_loading.py
import requests
import torch

from PIL import Image
from transformers import MllamaForConditionalGeneration, AutoProcessor
from huggingface_hub import login

from assurhabitat_agents.config.LLM_config import HF_TOKEN, BASE_MODEL, MAX_NEW_TOKENS

login(token=HF_TOKEN)

model_id = "meta-llama/Llama-3.2-11B-Vision-Instruct"

model = MllamaForConditionalGeneration.from_pretrained(
    model_id,
    torch_dtype=torch.bfloat16,
    device_map="auto",
)
processor = AutoProcessor.from_pretrained(model_id)

def vlm_inference(image, text="Just analyze the picture."):
    messages = [
        {"role": "user", "content": [
            {"type": "image"},
            {"type": "text", "text": text}
        ]}
    ]
    
    input_text = processor.apply_chat_template(messages, add_generation_prompt=True)
    inputs = processor(
        image,
        input_text,
        add_special_tokens=False,
        return_tensors="pt"
    ).to(model.device)
    
    output = model.generate(**inputs, max_new_tokens=30)
    
    return processor.decode(output[0])
