from langchain.sql_database import SQLDatabase
def connect_to_db(server: str, database: str) -> SQLDatabase:
    """Connect to SQL Server database"""
    db_uri = f"mssql+pyodbc://{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
    return SQLDatabase.from_uri(db_uri)