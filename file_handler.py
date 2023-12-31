import os
import re
from docx import Document
import fitz  # PyMuPDF
from striprtf.striprtf import rtf_to_text
import logging
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter

def is_valid_file_path(path):
    pattern = r'^[a-zA-Z0-9_\\-\\\\/:. ]+$'
    return re.match(pattern, path) and os.path.isfile(path)

def load_document(file_path):
    if not is_valid_file_path(file_path):
        raise ValueError(f"Invalid file path: {file_path}")
    
    file_extension = os.path.splitext(file_path)[1].lower()
    text = ""

    if file_extension == ".pdf":
        with fitz.open(file_path) as doc:
            text = "\n".join(page.get_text() for page in doc)
    elif file_extension == ".docx":
        doc = Document(file_path)
        text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
    elif file_extension == ".rtf":
        with open(file_path, 'r', encoding='utf-8') as file:
            rtf_text = file.read()
        text = rtf_to_text(rtf_text)
    elif file_extension == ".txt":
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
    else:
        raise ValueError(f"Unsupported file extension: {file_extension}")

    return text

def save_summary(summary, file_path):
    try:
        if file_path.endswith('.txt'):
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(summary)

        elif file_path.endswith('.docx'):
            doc = Document()
            doc.add_paragraph(summary)
            doc.save(file_path)

        elif file_path.endswith('.pdf'):
            pdf = SimpleDocTemplate(file_path, pagesize=letter)
            styles = getSampleStyleSheet()
            summary_paragraph = Paragraph(summary, styles['Normal'])
            pdf.build([summary_paragraph])

        else:
            raise ValueError("Unsupported file format selected.")

    except Exception as e:
        logging.error(f"An error occurred while saving the file: {e}")
        raise RuntimeError(f"An error occurred while saving the file: {e}")

    logging.info(f"Summary saved successfully to {file_path}")
