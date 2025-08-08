import pandas as pd
import chardet
import csv
from pathlib import Path
import os

def import_data():
    """
    Load the most recent CSV or Excel file from the 'artifact' folder.
    If multiple files exist, keep only the newest one and delete the rest.
    Returns:
        pandas.DataFrame
    """
    artifact_dir = Path(__file__).parent / "artifact"
    if not artifact_dir.exists():
        raise ValueError("Artifact folder does not exist")

    # Supported file extensions
    supported_extensions = ['.csv', '.txt', '.xlsx', '.xls']
    files = [f for f in artifact_dir.iterdir() if f.suffix.lower() in supported_extensions]

    if not files:
        raise ValueError("No CSV or Excel files found in artifact folder")

    # Find newest file
    newest_file = max(files, key=lambda f: f.stat().st_mtime)

    # Remove old files
    for f in files:
        if f != newest_file:
            try:
                os.remove(f)
                print(f"Deleted old file: {f.name}")
            except Exception as e:
                print(f"Could not delete {f.name}: {e}")

    filename_lower = newest_file.name.lower()

    # CSV / TXT handling
    if filename_lower.endswith(('.csv', '.txt')):
        with open(newest_file, 'rb') as f:
            encoding = chardet.detect(f.read())['encoding'] or 'utf-8'

        try:
            with open(newest_file, 'r', encoding=encoding, errors='replace') as f:
                sample = f.read(4096)
                delimiter = csv.Sniffer().sniff(sample, delimiters=[',', ';', '\t', '|']).delimiter
        except:
            delimiter = ','

        df = pd.read_csv(newest_file, encoding=encoding, delimiter=delimiter,
                        low_memory=False, on_bad_lines='skip')

    # Excel handling
    elif filename_lower.endswith(('.xlsx', '.xls')):
        engine = 'openpyxl' if filename_lower.endswith('.xlsx') else 'xlrd'
        df = pd.read_excel(newest_file, engine=engine)

    else:
        raise ValueError("Unsupported file format")

    if df.empty:
        raise ValueError("File is empty")

    print(f"Loaded: {newest_file.name} | Shape: {df.shape}")
    return df
