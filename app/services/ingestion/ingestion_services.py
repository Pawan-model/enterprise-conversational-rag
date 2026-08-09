from .extractors.pdf import extract_text
from ..chunk_services import split_text

def ingest_document(file_path:str)->list[str]:
    pages= extract_text(file_path)
    chunks=split_text(pages=pages)
    return chunks