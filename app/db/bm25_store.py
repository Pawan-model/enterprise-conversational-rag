from rank_bm25 import BM25Okapi
from app.models.document_chunk import DocumentChunk
bm25_index = None
bm25_chunks = []

def build_bm25_index(chunks):
    tokenized_chunks = []

    for chunk in chunks:
        tokens = chunk.content.lower().split()
        tokenized_chunks.append(tokens)

    bm25 = BM25Okapi(tokenized_chunks)

    return bm25

def search_bm25( query, limit=5):
    query_tokens=query.lower().split()
    scores=bm25_index.get_scores(query_tokens)
    ranked_indices=sorted(range(len(scores)),key=lambda i : scores[i],reverse=True)
    results=[]

    for index in ranked_indices[:limit]:
        if scores[index]>0:
            results.append(bm25_chunks[index])
    return results

def rebuild_bm25_index(chunks):
    global bm25_chunks,bm25_index

    bm25_chunks=chunks 
    bm25_index=build_bm25_index(chunks)
    
def initialize_bm25(db):
    chunks = db.query(DocumentChunk).all()
    rebuild_bm25_index(chunks)