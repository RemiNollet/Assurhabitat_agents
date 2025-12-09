"""#src/assurhabitat_agents/model/vlm_model_loading.py
import requests
import torch

from PIL import Image
from transformers import MllamaForConditionalGeneration, AutoProcessor
from huggingface_hub import login

from assurhabitat_agents.config.model_config import HF_TOKEN, VLM_BASE_MODEL

login(token=HF_TOKEN)

model = MllamaForConditionalGeneration.from_pretrained(
    VLM_BASE_MODEL,
    torch_dtype=torch.bfloat16,
    device_map="auto"
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
"""

from transformers import AutoProcessor, AutoModelForVision2Seq
import torch
from PIL import Image
from huggingface_hub import login

from assurhabitat_agents.config.model_config import HF_TOKEN, VLM_BASE_MODEL

login(token=HF_TOKEN)

device = "cuda" if torch.cuda.is_available() else "cpu"

processor = AutoProcessor.from_pretrained(VLM_BASE_MODEL)
model = AutoModelForVision2Seq.from_pretrained(
    VLM_BASE_MODEL,
    dtype=torch.float16,
    device_map="auto"
)

def vlm_inference(image, text):
    messages = [
        {"role": "user", "content": [
            {"type": "image"},
            {"type": "text", "text": text}
        ]}
    ]
    
    prompt = processor.apply_chat_template(messages, add_generation_prompt=True)
    inputs = processor(prompt, image, return_tensors="pt").to(device)
    generated_ids = model.generate(**inputs, max_new_tokens=30)
    output = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
    return output
