import os
from dotenv import load_dotenv
from langfuse import observe, Langfuse

load_dotenv()

LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

if not LANGFUSE_PUBLIC_KEY or not LANGFUSE_SECRET_KEY:
    raise ValueError(
        "Missing Langfuse credentials. Please set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in your environment."
    )

# --- CLIENT ---
langfuse = Langfuse(
    public_key=LANGFUSE_PUBLIC_KEY,
    secret_key=LANGFUSE_SECRET_KEY,
    host=LANGFUSE_HOST
)

# --- DECORATOR À IMPORTER ---
observe = observe  # re-export propre

__all__ = ["observe", "langfuse"]