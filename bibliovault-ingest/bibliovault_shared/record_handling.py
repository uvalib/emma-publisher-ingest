import xml.etree.ElementTree as ET
import logging

from bibliovault_shared import config, metadata
from opensearchpy.exceptions import ConnectionError
from shared import globals
from shared.UpsertHandler import UpsertHandler
from shared import globals as my_globals

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_text(node) :
    if (node is not None) :
        return node.text
    return ""

def process_file_as_string(file_contents):
    """
    Get records from IA
    Transform the records to EMMA format
    Send them to EMMA
    """
    emma_records = []
    num_read = 0
    num_records = 0
    
    namespaces = {'onix': 'http://ns.editeur.org/onix/3.0/reference'}
    root = ET.fromstring(file_contents)
    sentdate = get_text(root.find('.//onix:SentDateTime', namespaces))    
    
    my_globals.upsert_handler = UpsertHandler(my_globals.opensearch_conn)
    try:
        for item in root.findall('.//onix:Product', namespaces):
            num_read += 1
            # is_openaccess = re.search(pattern, line)
            # is_article = re.search(pattern2, line)
            # if (is_article and is_openaccess) :
            #     oa_record = json.loads(line)
            emma_record = metadata.transform_records([item], sentdate, globals.doc_validator)
            emma_records.extend(emma_record)
            if (len(emma_records) == config.EMMA_INGESTION_LIMIT):
                if my_globals.upsert_handler != None : 
                    my_globals.upsert_handler.submit_in_batch(emma_records, config.EMMA_INGESTION_LIMIT)
                num_records += len(emma_records)
                emma_records = []
        if (len(emma_records) > 0) :
            if my_globals.upsert_handler != None : 
                my_globals.upsert_handler.submit_in_batch(emma_records, config.EMMA_INGESTION_LIMIT)
            num_records += len(emma_records)

    except ConnectionError as e:
        logger.exception("Connection error exiting")
        raise e
    except Exception as e:
        logger.exception("Transform and send failed. This set will be retried.")
        print("Exception:", e)
        raise e
    return num_read, num_records


