import os
import docx
from PyPDF2 import PdfReader
from html.parser import HTMLParser

class TextStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []
    def handle_data(self, data):
        self.fed.append(data)
    def get_data(self):
        return "".join(self.fed)

def get_clean_text_from_html(file_name : str) -> str:
    # Your Word-exported HTML string
    with open(file_name, "r", encoding="utf-8", errors="replace") as f:
        html_content = f.read()

    # Strip tags using built-in Python (Zero Bloat)
    stripper = TextStripper()
    stripper.feed(html_content)
    clean_text = stripper.get_data()
    return clean_text
def docx_to_text(file_path: str) -> str:
    """Extracts text from a .docx file."""
    try:
        document = docx.Document(file_path)
        return "".join([para.text for para in document.paragraphs])
    except Exception as e:
        # Assuming logger is configured elsewhere or passed in
        print(f"Error reading docx file {file_path}: {e}")
        raise

def pdf_to_text(file_path: str) -> str:
    """Extracts text from a .pdf file."""
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        print(f"Error reading PDF file {file_path}: {e}")
        raise

def read_text_file(file_path: str) -> str:
    """Reads a plain text file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading text file {file_path}: {e}")
        raise

def file_to_text_factory(file_path: str) -> str:
    """
    Factory function that reads a file and returns its text content.
    It delegates to the appropriate function based on file extension.
    """
    extension = os.path.splitext(file_path)[1].lower()
    
    if extension in [".html", ".htm"]:
        return get_clean_text_from_html(file_path)
    elif extension == ".docx":
        return docx_to_text(file_path)
    elif extension == ".pdf":
        return pdf_to_text(file_path)
    elif extension == ".txt":
        return read_text_file(file_path)
    elif extension == ".doc":
        # python-docx does not support .doc files.
        # Informing the user about this limitation.
        raise NotImplementedError(".doc files are not supported. Please convert to .docx first.")
    else:
        # For any other file type, try to read as plain text.
        # This might not work for all binary files, but it's a fallback.
        print(f"Unsupported file type '{extension}', attempting to read as plain text.")
        return read_text_file(file_path)

