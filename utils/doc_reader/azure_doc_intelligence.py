import os
import re
import json
import logging
import traceback

from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult


import os
import sys
# Get the current working directory and add the parent directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from config.config import Configuration as config

logger = logging.getLogger(__file__)

class AzureDocumentIntelligenceLayoutAnalysis:
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.auth_config_azure = config.get_auth_config_azure_doc_intelligence()

    def extract_required_metadata(paragraphs, sections, tables, figures):
        
        page_wise_elements = {}
        
        try:
            elements = []
            page_numbers = []
            
            raw_paragraphs = {}
            raw_tables = {}
            raw_figures = {}
            
            # creating a list of page numbers
            for para in paragraphs:
                page_numbers.append(para['boundingRegions'][0]['pageNumber'])
            page_numbers = list(set(page_numbers))  
            
            # creating a dictionary of paragraphs, tables and figures with their respective index as key
            i = 0
            for para in paragraphs:
                raw_paragraphs[i] = para
                i+=1
            
            i = 0
            for table in tables:
                raw_tables[i] = table
                i+=1
            
            i = 0
            for figure in figures:
                raw_figures[i] = figure
                i+=1
            
            # extracting elements from sections. These elements follow the readability order of the page. It leaves out certain components like page numbers, headers, footers etc.   
            for spans in sections:
                elements.append(spans['elements'])
            
            elements.pop(0)
            sections = []
            kinds = []
            for element in elements:
                section = []
                kind = []
                for ele in element:
                    
                    if 'tables' in ele:
                        # find the number in the string
                        number = re.findall(r'\d+', ele)[0]
                        # append the table to the section
                        section.append(raw_tables[int(number)])
                        # remove the table from the raw_tables dictionary
                        raw_tables.pop(int(number))
                        # append the kind of element to the kind list
                        kind.append('tables')
                        
                    if 'paragraphs' in ele:
                        # find the number in the string
                        number = re.findall(r'\d+', ele)[0]
                        # append the paragraph to the section
                        section.append(raw_paragraphs[int(number)])
                        # remove the paragraph from the raw_paragraphs dictionary
                        raw_paragraphs.pop(int(number))
                        # append the kind of element to the kind list
                        kind.append('paragraphs')
                        
                    if 'figures' in ele:
                        # find the number in the string
                        number = re.findall(r'\d+', ele)[0]
                        # append the figure to the section
                        section.append(raw_figures[int(number)])
                        # remove the figure from the raw_figures dictionary
                        raw_figures.pop(int(number))
                        # append the kind of element to the kind list
                        kind.append('figures')
                
                sections.append(section)
                kinds.append(kind)
            
            # appending rmeaining paragraphs, tables and figures to the sections and kinds list, this captures images with no text, headers, footers, page numbers, etc.
            if len(raw_paragraphs) > 0:
                for key in raw_paragraphs.keys():
                    section = []
                    section.append(raw_paragraphs[key])
                    sections.append(section)
                    kinds.append(['paragraphs'])
                    
            if len(raw_tables) > 0:
                for key in raw_tables.keys():
                    section = []
                    section.append(raw_tables[key])
                    sections.append(section)
                    kinds.append(['tables'])
                    
            if len(raw_figures) > 0:
                for key in raw_figures.keys():
                    section = []
                    section.append(raw_figures[key])
                    sections.append(section)
                    kinds.append(['figures'])
                    
            for page in page_numbers:
                page_wise_elements[page] = {}
            
            j = 0   
            for section, kind in zip(sections, kinds):
                for sec, ki in zip(section, kind):
                    page_number = sec['boundingRegions'][0]['pageNumber']
                    page_wise_elements[page_number][j] = sec 
                    page_wise_elements[page_number][j]['kind_element'] = ki
                    j+=1
        
        except Exception as e:
            print("Error is in function extract_required_metadata. Error is {}".format(e))
            print(traceback.format_exc())
                
        return page_wise_elements

    def extract_table_content(tables):
        table_lists = []
        
        try:
            table_data = {}
            # Extracting table data
            column_count = tables['columnCount']
            # creating a list of empty strings with length equal to the number of columns in the table
            cell_list = [''] * column_count
            
            for cell in tables['cells']:
                # Extracting row index, column index and content of the cell
                row_index = cell.get('rowIndex')
                col_index = cell.get('columnIndex')
                content = cell.get('content')
                # Adding the content to the cell_list at the respective column index
                table_data.setdefault(row_index, {})[col_index] = content
                
            # Creating a list of dictionaries with each dictionary representing a row in the table
            for keys in table_data.keys():
                for key in table_data[keys].keys():
                    cell_list[key] = table_data[keys][key]
                table_lists.append(cell_list.copy())
                
        except Exception as e:
            print("Error is in function extract_table_content. Error is {}".format(e))
            print(traceback.format_exc())
        return table_lists

    def extract_figure_content(figures, raw_paragraphs):
        figure_text = ''
        try:
            if 'elements' in figures:
                for ele in figures['elements']:
                    # find the number in the string
                    number = re.findall(r'\d+', ele)[0]
                    # append the figure to the section
                    figure_text += raw_paragraphs[int(number)]['content'] + ' '
                    
        except Exception as e:
            print("Error is in function extract_figure_content. Error is {}".format(e))
            print(traceback.format_exc())
        return figure_text

    def page_wise_content(section_wise_elements, raw_paragraphs):
                
        page_wise_content = {}
        try:
            # iterating through the pages
            for pages in section_wise_elements.keys():
                page_wise_content[pages] = {}
                
                # iterating through the sections in the page
                for section in section_wise_elements[pages].keys():
                    page_wise_content[pages][section] = {}
                    
                    # extracting content from the sections
                    if section_wise_elements[pages][section]['kind_element'] == 'tables':
                        table_information = AzureDocumentIntelligenceLayoutAnalysis.extract_table_content(section_wise_elements[pages][section])
                        page_wise_content[pages][section]['content'] = table_information
                        page_wise_content[pages][section]['kind_element'] = 'tables'
                        if 'caption' in section_wise_elements[pages][section]:
                            page_wise_content[pages][section]['caption'] = section_wise_elements[pages][section]['caption']['content']
                            
                        
                    elif section_wise_elements[pages][section]['kind_element'] == 'paragraphs':
                        text_information = section_wise_elements[pages][section]['content']
                        page_wise_content[pages][section]['content'] = text_information
                        if 'role' in section_wise_elements[pages][section]:
                            page_wise_content[pages][section]['kind_element'] = section_wise_elements[pages][section]['role']
                        else:
                            page_wise_content[pages][section]['kind_element'] = 'paragraphs'
                        
                        
                    elif section_wise_elements[pages][section]['kind_element'] == 'figures':
                        figure_information = AzureDocumentIntelligenceLayoutAnalysis.extract_figure_content(section_wise_elements[pages][section], raw_paragraphs)
                        page_wise_content[pages][section]['content'] = figure_information
                        page_wise_content[pages][section]['kind_element'] = 'figures'
                        if 'caption' in section_wise_elements[pages][section]:
                            page_wise_content[pages][section]['caption'] = section_wise_elements[pages][section]['caption']['content']
                            
        except Exception as e:
            print("Error is in function page_wise_content. Error is {}".format(e))
            print(traceback.format_exc())
            
        return page_wise_content

    def azure_document_intelligence_layout(self):
        
        final_parsed_output = {}
        
        try:
            
            downloaded_pdf_file_path = self.file_path
            
            azure_doc_endpoint = self.auth_config_azure['azure_doc_endpoint']
            document_intelligence_azure_api_key =  AzureKeyCredential(self.auth_config_azure['doc_intelligence_azure_api_key'])
            document_intelligence_client = DocumentIntelligenceClient(azure_doc_endpoint, document_intelligence_azure_api_key)
            
            # Analyzing the document using Azure Document Intelligence
            with open(downloaded_pdf_file_path, "rb") as f:
                poller = document_intelligence_client.begin_analyze_document(
                    "prebuilt-layout", analyze_request=f, content_type="application/octet-stream"
                )

            raw_output: AnalyzeResult = dict(poller.result())
            raw_output = str(raw_output)
            raw_output = eval(raw_output)

            raw_paragraphs = raw_output['paragraphs']
            raw_tables = raw_output['tables']
            raw_sections = raw_output['sections']
            raw_figures = raw_output['figures']
            
            section_wise_elements = AzureDocumentIntelligenceLayoutAnalysis.extract_required_metadata(raw_paragraphs, raw_sections, raw_tables, raw_figures)
            final_parsed_output = AzureDocumentIntelligenceLayoutAnalysis.page_wise_content(section_wise_elements, raw_paragraphs)
            
        except Exception as e:
            print("Error is in function azure_document_intelligence_layout. Error is {}".format(e))
            print(traceback.format_exc())
            
        return final_parsed_output
        
def azure_parsed_pdf(file_path: str):
    
    azure_doc_intelligence = AzureDocumentIntelligenceLayoutAnalysis(file_path)
    final_document_parsed_output = azure_doc_intelligence.azure_document_intelligence_layout()
    
    return final_document_parsed_output 