from .. import database as backend

def get_data():
    return backend.fetch_data()
