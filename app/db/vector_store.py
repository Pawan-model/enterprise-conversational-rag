from qdrant_client import QdrantClient
from qdrant_client.http import models

client = QdrantClient(path="./qdrant_data")

COLLECTION_NAME = "documents"

def init_vector_db():
    """
    Checks if the collection exists. If not, it creates it with the correct rules.
    """
    
    collections = client.get_collections().collections
    exists = any(col.name == COLLECTION_NAME for col in collections)

    if not exists:
        
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size = 384,
                distance = models.Distance.COSINE
            )
        )
        print(f"Vector collection '{COLLECTION_NAME}' created successfully.")
    else:
        print(f"Vector collection '{COLLECTION_NAME}' already exists.")


def insert_vector(point_id: int,
                  vector: list[float],
                  document_id: int,
                  filename: str,
                  page_number: int,
                  chunk_index: int,
                  content: str):
    """
    Takes a generated vector and its metadata and saves it to Qdrant.
    """
    point = models.PointStruct(id=point_id, vector=vector, payload={"document_id":document_id,
                                                                    "filename":filename,
                                                                    "page_number":page_number,
                                                                    "chunk_index":chunk_index,
                                                                      "content": content})

    client.upsert(collection_name=COLLECTION_NAME, points=[point])

    print(f"Successfully inserted vector for document {document_id} into Qdrant.")


def search_vectors(query_vector: list[float], limit: int= 5):
    """
    Searches Qdrant for the most similar vectors to the provided query.
    """

    results = client.query_points(collection_name=COLLECTION_NAME,query=query_vector,limit=limit)
    filtered_result=[]
    for point in results.points:
        if point.score >=0.5:
            filtered_result.append(point)

    return filtered_result


def delete_vector(point_ids:list[int]):
    """takes the point_id and delete its corresponding vector"""
    client.delete(collection_name=COLLECTION_NAME,points_selector=models.PointIdsList(points=point_ids))
