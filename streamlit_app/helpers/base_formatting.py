from datetime import date, datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment


def formatting_page(ws, max_row=None, max_col=None):
    """
    Apply default formatting to the worksheet:
      - hide ALL gridlines (view and print)
      - apply a clean Calibri font, white fill, centered alignment

    Parameters:
    ws (Worksheet): The openpyxl worksheet object.
    max_row (int, optional): Maximum row to process (defaults to ws.max_row).
    max_col (int, optional): Maximum column to process (defaults to ws.max_column).
    """
    # determine processing bounds
    if max_row is None:
        max_row = ws.max_row
    if max_col is None:
        max_col = ws.max_column

    # hide gridlines in the sheet view
    ws.sheet_view.showGridLines = False
    # hide gridlines when printing
    ws.print_options.gridLines = False

    # define styles (no borders)
    default_font      = Font(name='Calibri', size=11)
    default_fill      = PatternFill(fill_type='solid', start_color='FFFFFF')
    default_alignment = Alignment(horizontal='center', vertical='center')

    # apply styles + date formatting
    for row in ws.iter_rows(min_row=1, max_row=max_row, min_col=1, max_col=max_col):
        for cell in row:
            cell.font      = default_font
            cell.fill      = default_fill
            cell.alignment = default_alignment

            if cell.value is None:
                continue
            