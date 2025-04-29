import pandas as pd
import matplotlib.pyplot as plt
import sys
from pathlib import Path

def read_spreadsheet(file_path):
    """
    Read spreadsheet data from either .xlsx or .csv file
    """
    file_path = Path(file_path)
    if file_path.suffix.lower() == '.xlsx':
        return pd.read_excel(file_path)
    elif file_path.suffix.lower() == '.csv':
        return pd.read_csv(file_path)
    else:
        raise ValueError("Unsupported file format. Please use .xlsx or .csv files.")

def create_graph(data, x_column, y_column, graph_type='line', title=None, output_file=None):
    """
    Create a graph from the spreadsheet data
    """
    plt.figure(figsize=(10, 6))
    
    if graph_type.lower() == 'line':
        plt.plot(data[x_column], data[y_column], marker='o')
    elif graph_type.lower() == 'bar':
        plt.bar(data[x_column], data[y_column])
    elif graph_type.lower() == 'scatter':
        plt.scatter(data[x_column], data[y_column])
    else:
        raise ValueError("Unsupported graph type. Use 'line', 'bar', or 'scatter'")

    plt.title(title or f'{y_column} vs {x_column}')
    plt.xlabel(x_column)
    plt.ylabel(y_column)
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()

    if output_file:
        plt.savefig(output_file)
    else:
        plt.show()

def main():
    if len(sys.argv) < 4:
        print("Usage: python test.py <spreadsheet_file> <x_column> <y_column> [graph_type] [output_file]")
        print("Example: python test.py data.xlsx 'Date' 'Sales' line 'graph.png'")
        sys.exit(1)

    try:
        # Get command line arguments
        file_path = sys.argv[1]
        x_column = sys.argv[2]
        y_column = sys.argv[3]
        graph_type = sys.argv[4] if len(sys.argv) > 4 else 'line'
        output_file = sys.argv[5] if len(sys.argv) > 5 else None

        # Read the spreadsheet
        data = read_spreadsheet(file_path)

        # Verify columns exist
        if x_column not in data.columns or y_column not in data.columns:
            print(f"Error: Columns not found. Available columns: {', '.join(data.columns)}")
            sys.exit(1)

        # Create the graph
        create_graph(data, x_column, y_column, graph_type, output_file=output_file)
        print("Graph created successfully!")

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
