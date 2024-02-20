from docx import Document
import webcolors
from docx.oxml.ns import qn
def closest_color(hex_color):
    """ Function to find the closest color name for a given hex color """
    try:
        color_name = webcolors.hex_to_name(hex_color)
    except ValueError:
        try:
            closest_hex = webcolors.hex_to_rgb(hex_color)
            color_name = webcolors.rgb_to_name(closest_hex)
        except ValueError:
            color_name = hex_color  # If no close match is found, return the hex color
    return color_name

def get_cell_color(cell):
    """ Function to extract the color information of a specified cell """
    shading = cell._element.xpath('.//w:shd')
    return shading[0].get(qn('w:fill')) if shading else None

# Load the Word document
doc = Document('NLP_ORs_example_results_1.0.docx')

# Iterate through each table in the document
for table_index, table in enumerate(doc.tables):
    print(f"Table {table_index + 1}:")
    for row_index, row in enumerate(table.rows):
        for cell_index, cell in enumerate(row.cells):
            hex_color = get_cell_color(cell)
            color_name = closest_color(hex_color) if hex_color else "No color"
            print(f"Cell ({row_index + 1}, {cell_index + 1}): {color_name}")
    print("\n")  # Add a newline for better separation between tables

