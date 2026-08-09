from fastapi import FastAPI
from app.api.routes.health import router as health_router
from app.api.routes.documents import router as document_router
from app.db.session import Base, engine,sessionLocal
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.db.vector_store import init_vector_db
from app.db.bm25_store import initialize_bm25
from app.models.conversation import Conversation
from app.models.message import Message

app=FastAPI(title="Enterprise RAG API", version="0.1.0")
Base.metadata.create_all(bind=engine)
init_vector_db()
db = sessionLocal()

try:
    initialize_bm25(db)
finally:
    db.close()
app.include_router(health_router,tags=["Health"])

app.include_router(document_router,prefix="/documents",tags=['Document'])
