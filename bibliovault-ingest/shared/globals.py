import os
from shared.DocValidator import DocValidator

#  Globals
INGESTION_SCHEMA_FILE = 'ingestion-record.schema.json' if os.path.exists('ingestion-record.schema.json') \
        else 'ingestion/ingestion-record.schema.json'

doc_validator = DocValidator(schema_file_name=INGESTION_SCHEMA_FILE)
opensearch_conn = None
upsert_handler = None

botocore_session = None 
dynamo_table = None
debug = False
terminate_flag = False 

DEFAULT_OPENSEARCH_HOST = 'vpc-emma-index-production-glc53yq4angokfgqxlmzalupqe.us-east-1.es.amazonaws.com:443'
DEFAULT_OPENSEARCH_INDEX = 'emma-federated-index-production'
