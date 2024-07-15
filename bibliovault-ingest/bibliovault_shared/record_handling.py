import xml.etree.ElementTree as ET
import logging

from bibliovault_shared import config, metadata
from shared.helpers import batch
from opensearchpy import helpers as helpers2
from opensearchpy.exceptions import ConnectionError
from shared import globals
from ingestion_validator.UpsertHandler import UpsertHandler

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
                if globals.opensearch_conn != None : 
                    batch_direct_to_opensearch(emma_records, config.EMMA_INGESTION_LIMIT, None, globals.opensearch_conn)
                # else : 
                #     batch_to_ingestion(emma_records, config.EMMA_INGESTION_LIMIT, emma_ingestion_url)
                num_records += len(emma_records)
                emma_records = []
        if (len(emma_records) > 0) :
            if globals.opensearch_conn != None : 
                batch_direct_to_opensearch(emma_records, config.EMMA_INGESTION_LIMIT, None, globals.opensearch_conn)
            # else : 
            #     batch_to_ingestion(emma_records, config.EMMA_INGESTION_LIMIT, emma_ingestion_url)
            num_records += len(emma_records)

    except ConnectionError as e:
        logger.exception("Connection error exiting")
        raise e
    except Exception as e:
        logger.exception("Transform and send failed. This set will be retried.")
        print("Exception:", e)
        raise e
    return num_records


def batch_direct_to_opensearch(emma_records, num_per_batch, doc_validator, opensearch_conn):
    
    index = globals.opensearch_conn.index
    handler = UpsertHandler(globals.opensearch_conn.index, doc_validator)
    for records in batch(emma_records, num_per_batch):
        logger.info("Sending smaller batch of  " + str(len(records)) + " records to opensearch index " + index + " directly")
        bulk_upsert = []
        for record in records :
            upsert_doc = handler.create_upsert_doc(opensearch_conn, record)
            bulk_upsert.append(upsert_doc)
            # doc_count = doc_count + 1

        # handler.logger.info(json.dumps(records))

        helpers2.bulk(opensearch_conn.connection, bulk_upsert)

