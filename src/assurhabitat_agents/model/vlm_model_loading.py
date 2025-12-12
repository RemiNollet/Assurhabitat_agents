# src/assurhabitat_agents/model/vlm_model_loading.py

import torch
from functools import lru_cache
from transformers import AutoProcessor, AutoModelForImageTextToText
from huggingface_hub import login
from qwen_vl_utils import process_vision_info

from assurhabitat_agents.config.model_config import HF_TOKEN, VLM_BASE_MODEL
from assurhabitat_agents.config.langfuse_config import observe

device = "cuda" if torch.cuda.is_available() else "cpu"


@lru_cache(maxsize=1)
def load_vlm():
    """Load processor + model once"""
    processor = AutoProcessor.from_pretrained(VLM_BASE_MODEL)
    model = AutoModelForImageTextToText.from_pretrained(
        VLM_BASE_MODEL,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        device_map="auto",
        offload_buffers=True,
    )
    return processor, model

@observe(name="vlm inference")
def vlm_inference(image_path: list[str], text: str):
    processor, model = load_vlm()

    # Build multimodal content block
    # contents = [{"type": "image", "image": p} for p in image_paths]
    # contents.append({"type": "text", "text": text})

    # messages = [{"role": "user", "content": contents}]
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image_path},
                {"type": "text", "text": text},
            ],
        }
    ]

    # Step 1: prepare the chat template
    prompt = processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )

    # Step 2: extract vision inputs (VERY IMPORTANT)
    image_inputs, video_inputs = process_vision_info(messages)

    # Step 3: processor merges text + images into model inputs
    inputs = processor(
        text=[prompt],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    ).to(model.device)

    # Step 4: generate
    output_ids = model.generate(**inputs, max_new_tokens=128)

    # Remove prompt part
    trimmed = [
        out[len(inp):] for inp, out in zip(inputs.input_ids, output_ids)
    ]

    # Step 5: decode
    return processor.batch_decode(
        trimmed,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False
    )[0]