"""
File Parser - Handles different file types
"""

from typing import Optional
import io


def parse_file_content(file_content: bytes, filename: str) -> str:
    """
    Parse file content based on file extension.
    Returns extracted text content.
    """
    filename_lower = filename.lower()
    
    # Text files
    if filename_lower.endswith(('.txt', '.md', '.markdown')):
        try:
            return file_content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                return file_content.decode('latin-1')
            except:
                return file_content.decode('utf-8', errors='ignore')
    
    # PDF files
    elif filename_lower.endswith('.pdf'):
        try:
            import PyPDF2
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except ImportError:
            raise ValueError("PyPDF2 is required for PDF files. Install with: pip install PyPDF2")
        except Exception as e:
            raise ValueError(f"Error parsing PDF: {str(e)}")
    
    # DOCX files
    elif filename_lower.endswith(('.docx', '.doc')):
        try:
            from docx import Document
            doc_file = io.BytesIO(file_content)
            doc = Document(doc_file)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except ImportError:
            raise ValueError("python-docx is required for DOCX files. Install with: pip install python-docx")
        except Exception as e:
            raise ValueError(f"Error parsing DOCX: {str(e)}")
    
    # Default: try to decode as text
    else:
        try:
            return file_content.decode('utf-8')
        except:
            try:
                return file_content.decode('latin-1')
            except:
                return file_content.decode('utf-8', errors='ignore')

