from langchain_text_splitters import RecursiveCharacterTextSplitter

def split_text(pages:list[dict],chunk_size:int=500, chunk_overlap:int=100)->list[dict]:
    splitter=RecursiveCharacterTextSplitter(chunk_size=chunk_size,chunk_overlap=chunk_overlap)
    final_chunks=[]
    for page in pages:
        page_chunk=splitter.split_text(page['text'])
        for chunk in page_chunk:
            chunk_info={"page":page["page"],
                  "text":chunk}
            final_chunks.append(chunk_info)
    return final_chunks


    
