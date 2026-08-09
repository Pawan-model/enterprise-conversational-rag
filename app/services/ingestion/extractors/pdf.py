import fitz
import os

def extract_text(file_path: str) -> list[dict]:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f'the directory {file_path} does not exist')  
    
    pages=[]

    try:
        with fitz.open(file_path) as document:

            for page_num in range(len(document)):
                page=document.load_page(page_num)
                page_text=page.get_text()

                if page_text:
                    pages.append({"page": page_num+1,
                                  "text":page_text})
                else:
                    continue
    except Exception as e:
        raise RuntimeError(f"An error occurred while parsing the PDF: {str(e)}")
        
    return pages