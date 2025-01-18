from utils.doc_writer.word_document import markdown_to_word

def file_writer(filename, content):
    if filename.split('.')[-1] == 'docx':
        markdown_to_word(markdown_content=content, word_file=filename)