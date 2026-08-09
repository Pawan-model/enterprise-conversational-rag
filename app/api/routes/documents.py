from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.conversation import Conversation
from app.models.message import Message
from app.db.session import get_db
from app.services.embedding import generate_embedding
from app.db.vector_store import insert_vector
from app.db.vector_store import search_vectors
from app.db.vector_store import delete_vector
from google import genai
import os
from dotenv import load_dotenv
import shutil
from app.services.ingestion.ingestion_services import ingest_document
from app.db.bm25_store import rebuild_bm25_index,search_bm25
from app.db.hybrid_retrieval import reciprocal_rank_fusion,get_hybrid_result


UPLOAD_DIR = "uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)

load_dotenv()

api_keys = os.getenv("GEMINI_API_KEY")

router = APIRouter()

gemini_client = genai.Client(api_key=api_keys)


@router.get("/")
def get_all_documents(db: Session=Depends(get_db)):
    documents = db.query(Document).all()
    return documents


@router.get("/search")
def search_documents(query:str,conversation_id:int,db:Session=Depends(get_db)):
    conversation=db.query(Conversation).filter(Conversation.id==conversation_id).first()
    if conversation is None:
        raise HTTPException(status_code=404, detail="conversation not found")
    messages=conversation.messages
    history = ""

    for message in messages:
        history += f"{message.role}: {message.content}\n"
    vector = generate_embedding(query)
    qdrant_results = search_vectors(vector)
    bm25_results=search_bm25(query=query)
    rrf_results=reciprocal_rank_fusion(qdrant_results=qdrant_results,bm25_results=bm25_results)
    hybrid_result=get_hybrid_result(rrf_results=rrf_results,db=db)


    content_block = []
    sources=[]

    for result in hybrid_result:
        content_block.append(f""" Source: {result['filename']},
         Page:{result['page_number']},
         Content:{result['content']} """)
        source={"filename":result["filename"],
                        "page_number":result["page_number"]}
        if source not in sources:
            sources.append(source)

    combined_context= "\n\n".join(content_block)
    prompt_template = f"""
You are an intelligent assistant answering questions about uploaded PDF documents.

Use ONLY the provided context to answer the user's question.

If the answer cannot be found in the provided context, say:
"I could not find the answer in the uploaded documents."

Do not make up information.

Conversation history:
{history}

Context:
{combined_context}

Question:
{query}
    """
    gemini_response = gemini_client.models.generate_content(model="gemini-3.5-flash", contents= prompt_template)

    user_message=Message(
        conversation_id=conversation_id,
        role="user",
        content=query
    )
    assistant_message=Message(
        conversation_id=conversation_id,
        role="assistant",
        content=gemini_response.text
    )
    db.add(user_message)
    db.add(assistant_message)
    db.commit()

    return {"answer" : gemini_response.text,
            "sources": sources}

@router.get("/{doc_id}")
def get_document(doc_id: int, db: Session=Depends(get_db)):
    document = db.query(Document).filter(Document.id==doc_id).first()
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    return document

@router.post("/upload_doc/")
async def upload_file(file:UploadFile=File(),db:Session=Depends(get_db)):
    duplicate=db.query(Document).filter(Document.filename==file.filename).first()
    if duplicate:
        raise HTTPException(status_code=409,detail="file already exists")
    
    file_path=os.path.join(UPLOAD_DIR,file.filename)
    with open(file_path,'wb') as buffer:
        shutil.copyfileobj(file.file,buffer)
    chunks=ingest_document(file_path)
    db_document=Document(filename=file.filename,filepath=file_path)
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    db_chunks=[]
    for chunk_index,chunk in enumerate(chunks):
        db_chunk=DocumentChunk(document_id=db_document.id,
                               chunk_index=chunk_index,
                               page_number=chunk['page'],
                               content=chunk["text"])
        db.add(db_chunk)
        db_chunks.append(db_chunk)
    db.commit()
    all_chunks = db.query(DocumentChunk).all()
    rebuild_bm25_index(all_chunks)
    for db_chunk in db_chunks:
        db.refresh(db_chunk)
        vector=generate_embedding(text=db_chunk.content)
        insert_vector(
    point_id=db_chunk.id,
    vector=vector,
    document_id=db_document.id,
    filename=db_document.filename,
    page_number=db_chunk.page_number,
    chunk_index=db_chunk.chunk_index,    
    content=db_chunk.content,)

    return {
    "document_id": db_document.id,
    "filename": db_document.filename,
    "chunks_saved": len(chunks),
    "status": "success"
}

@router.delete("/{doc_id}")
def delete_document(doc_id:int,db:Session=Depends(get_db)):
    document=db.query(Document).filter(Document.id==doc_id).first()
    if document is None:
        raise HTTPException(status_code=404, detail='document not found')
    chunks=document.chunks
    chunk_ids=[]

    for chunk in chunks:
        chunk_ids.append(chunk.id)
        db.delete(chunk)
    delete_vector(chunk_ids)
    if os.path.exists(document.filepath):
        os.remove(document.filepath)
    
    db.delete(document)
    db.commit()
    all_chunks = db.query(DocumentChunk).all()
    rebuild_bm25_index(all_chunks)
    return {
    "message": "Document deleted successfully",
    "document_id": doc_id
    }


@router.post("/conversations")
def create_conversation(db:Session=Depends(get_db)):
    conversation=Conversation()
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return {"conversation_id":conversation.id}