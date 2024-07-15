import os
from ingestion_validator.DocValidator import DocValidator

#  Globals
INGESTION_SCHEMA_FILE = 'ingestion-record.schema.json' if os.path.exists('ingestion-record.schema.json') \
        else 'ingestion/ingestion-record.schema.json'

doc_validator = DocValidator(schema_file_name=INGESTION_SCHEMA_FILE)
opensearch_conn = None
DEFAULT_OPENSEARCH_HOST = 'localhost:9001'
DEFAULT_OPENSEARCH_INDEX = 'emma-federated-index-staging-1.0.1'
        
