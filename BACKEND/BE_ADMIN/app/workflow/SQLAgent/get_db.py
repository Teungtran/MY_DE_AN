def connect_to_db(server: str, database: str) -> str:
    """Return the database URI for MSSQL connection"""
    db_uri = f"mssql+pyodbc://{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
    return db_uri

db_url = connect_to_db(server="DESKTOP-LU731VP\\SQLEXPRESS", database="DE_AN")