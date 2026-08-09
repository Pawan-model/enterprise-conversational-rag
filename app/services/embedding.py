from sentence_transformers import SentenceTransformer

model = SentenceTransformer(model_name_or_path="all-MiniLM-L6-v2")

def generate_embedding(text: str) -> list[float]:
    """
    Takes a string of text and generate 384-dimensional vector embedding
    """
    vector = model.encode(text)

    return vector.tolist()