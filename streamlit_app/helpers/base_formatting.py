from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment



def formatting_page(ws, max_row=100, max_col=50):
    """
    Apply default formatting (font, fill, border, alignment) to the entire worksheet.

    Parameters:
    ws (Worksheet): The openpyxl worksheet object.
    max_row (int): Maximum number of rows to format.
    max_col (int): Maximum number of columns to format.
    """
    # Define styles
    default_font = Font(name='Calibri', size=11)
    default_fill = PatternFill(fill_type='solid', start_color='FFFFFF')
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    default_alignment = Alignment(horizontal='center', vertical='center')

    # Apply styles
    for row in ws.iter_rows(min_row=1, max_row=max_row, min_col=1, max_col=max_col):
        for cell in row:
            cell.font = default_font
            cell.fill = default_fill
            cell.border = thin_border
            cell.alignment = default_alignment