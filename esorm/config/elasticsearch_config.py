import os

HOST = os.getenv('ES_HOST', 'localhost')
PORT = os.getenv('ES_PORT', 9200)
INDEX = 'orm'
TYPE = 'entity'
VERSIONING_INDEX = 'version'
VERSIONING_TYPE = 'orm_entity'
