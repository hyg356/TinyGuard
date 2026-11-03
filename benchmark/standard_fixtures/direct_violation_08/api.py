import database  # persistence dependency

def get_data():
    return database.fetch_data()
