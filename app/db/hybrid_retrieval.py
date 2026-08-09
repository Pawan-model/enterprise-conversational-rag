from app.models.document_chunk import DocumentChunk
def reciprocal_rank_fusion(qdrant_results, bm25_results, limit=5):
    scores = {}
    

    for rank, point in enumerate(qdrant_results,start=1):
        chunk_id = point.id
        
        scores[chunk_id]=scores.get(chunk_id,0)+1/(60+rank)

    for rank, chunk in enumerate(bm25_results, start=1):
        chunk_id = chunk.id

        scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (60 + rank)

    ranked_ids=sorted(scores,key=scores.get,reverse=True)
    final_results=[]
    for chunk_id in ranked_ids[:limit]:
        final_results.append({"chunk_id":chunk_id,
                              "score":scores[chunk_id]})
    return final_results


def normalize_result(item, score):
    if isinstance(item, DocumentChunk):
        return {           
    "chunk_id":item.id,
    "document_id":item.document_id,
    "filename": item.document.filename,
    "page_number": item.page_number,
    "content": item.content,
    "score": score
        }
    else:
        return {
    "chunk_id": item.id,
    "document_id": item.payload["document_id"],
    "filename": item.payload["filename"],
    "page_number": item.payload["page_number"],
    "content": item.payload["content"],
    "score": score
    }

def get_hybrid_result(rrf_results,db):
    final_results=[]
    for results in rrf_results:
        chunk_id=results["chunk_id"]
        score=results["score"]
        chunk=db.query(DocumentChunk).filter(DocumentChunk.id==chunk_id).first()
        if chunk is None:
            continue
        normalized_result=normalize_result(chunk,score)
        final_results.append(normalized_result)
    return final_results