from utils.doc_writer.docx_utils.docx_utils import * 
from utils.doc_writer.docx_utils.html_utils import * 

from docx import Document
import json
from io import BytesIO
import json 
import markdown2


def markdown_to_word(markdown_content, word_file):
    doc = Document()
    para = doc.add_paragraph()
    html_content = markdown2.markdown(markdown_content)
    soup = BeautifulSoup(html_content, 'html.parser')
    elements = parse_soup_to_elements(soup)
    insert_elements_after_paragraph(para, elements)
    doc.save(word_file)