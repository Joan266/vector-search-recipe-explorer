import os
import signal
from vertexai.language_models import TextEmbeddingModel, TextEmbeddingInput
import vertexai

# === Setup environment ===
PROJECT_ID = "my-vector-search-project"
REGION = "us-central1"

# Use the local JSON key (already set in Gitpod terminal or .env)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/workspace/ecoscan-mongodb/vertex-key.json"

# === Optional: timeout safeguard ===
def timeout_handler(signum, frame):
    raise TimeoutError("⚠️ Vertex AI took too long to respond.")
signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(60)  # max 60 seconds allowed

# === Init Vertex ===
print("🔌 Initializing Vertex AI...")
vertexai.init(project=PROJECT_ID, location=REGION)

print("📦 Loading model...")
model = TextEmbeddingModel.from_pretrained("gemini-embedding-001")
print("✅ Model loaded!")

text = "EcoScan is an AI-powered product matcher for sustainable items."
input_obj = TextEmbeddingInput(text, "RETRIEVAL_DOCUMENT")


# === Get embedding ===
print("📡 Sending request...")
embedding = model.get_embeddings([input_obj], output_dimensionality=768)

print("📈 Got embedding! Vector size:", len(embedding[0].values))
print("🔢 First few values:", embedding[0].values[:5])
