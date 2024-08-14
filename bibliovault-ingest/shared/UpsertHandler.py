"""
Handler for requests to update or add to the federated index.
"""
import uuid
import logging
import iso8601

# from shared2.alias_utils import rename_to_backwards_compatible_deprecated_fields
from shared.helpers import get_doc_id, get_today_iso8601_datetime_pst, exists, get_doc_id_prefix

def batch(iterable, batch_size=1):
    """
    Batches iterables in even batches of n length, until the last batch, which runs until the end.
    Batch size defaults to 1.
    """
    if batch_size < 1:
        raise ValueError(f"Batch size can not be less than 1: {batch_size}")
    length = len(iterable)
    for ndx in range(0, length, batch_size):
        yield iterable[ndx:min(ndx + batch_size, length)]

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class UpsertHandler:

    def __init__(self, opensearch_conn):
        # self.validator = validator
        self.opensearch_conn = opensearch_conn
        # Keep track of artifacts in same batch that might share title ID
        self.current_title_ids = {}

    def submit_in_batch(self, emma_records, num_per_batch):
    
        for records in batch(emma_records, num_per_batch):
            logger.info("Sending batch of  " + str(len(records)) + " records to opensearch index " + self.opensearch_conn.index + " directly")
            bulk_upsert = []
            for record in records :
                upsert_doc = self.create_upsert_doc(record)
                bulk_upsert.append(upsert_doc)
                # doc_count = doc_count + 1
    
            self.opensearch_conn.bulk(bulk_upsert)

    def clean_identifier(self, document):
        if exists(document, 'dc_identifier'):
            document['dc_identifier'] = [ str(ident).replace('-', '') for ident in document['dc_identifier'] ]
        if exists(document, 'dc_relation'):
            document['dc_relation'] = [ str(ident).replace('-', '') for ident in document['dc_relation'] ]

    def create_upsert_doc(self, document):
        doc_id = get_doc_id(document)
        document['emma_recordId'] = doc_id
        document['emma_indexLastUpdated'] = get_today_iso8601_datetime_pst()
        self.clean_identifier(document)
        self.truncate_publication_date(document)
        # rename_to_backwards_compatible_deprecated_fields(document)
        self.update_emma_title_id(document)
        upsert_doc = {
            '_op_type': 'update',
            '_index': self.opensearch_conn.index,
            '_id': doc_id,
            # "_type": "_doc",
            'pipeline': 'sortDate',
            'doc': document,
            'doc_as_upsert': True
        }
        return upsert_doc


    def update_emma_title_id(self, doc):
        """
        Attempt to see if there are other metadata records using the same industry-standard title identifiers.
        If so, share the emma_titleId.
        TODO: It may be more efficient to do periodic bulk updates rather than one at a time at load time.
        """
        id_list = self.get_identifier_list(doc)
        first_id = id_list[0]

        if not exists(doc, 'emma_titleId'):
            found = False
            for identifier in id_list:
                # Check current batch before ElasticSearch
                if exists(self.current_title_ids, identifier):
                    doc['emma_titleId'] = self.current_title_ids[identifier]
                    found = True
                    break
            # if not found:
            #     existing_title_id = self.get_title_id_elasticsearch(es, id_list)
            #     if existing_title_id is not None and len(existing_title_id) > 0:
            #         doc['emma_titleId'] = existing_title_id
            #         self.current_title_ids[first_id] = existing_title_id

        if not exists(doc, 'emma_titleId'):
            doc['emma_titleId'] = str(uuid.uuid4())
        
        self.current_title_ids[first_id] = doc['emma_titleId']

    def get_identifier_list(self, doc):
        """
        Build a list of identifiers to coalesce to the title id.
        """
        id_list = []
        if exists(doc, 'dc_identifier'):
            id_list.extend(doc['dc_identifier'])
        # No ISBN/OCLC/Industry standard?  Use repo ID + repo record ID
        id_list.append(get_doc_id_prefix(doc))
        if exists(doc, 'dc_relation'):
            id_list.extend(doc['dc_relation'])
        return id_list

    # def get_title_id_elasticsearch(self, es, identifier):
    #     """
    #     Try to find a title ID which matches the identifier
    #     """
    #     search = Search(using=es, index=self.index).query(
    #         "terms", dc_identifier__raw=identifier)
    #     # self.logger.info(search.to_dict())
    #
    #     eslogger = logging.getLogger("opensearch")
    #     esloggerlevel = eslogger.getEffectiveLevel()
    #     eslogger.setLevel(logging.WARN)
    #     try :  
    #         es_response = search.execute()
    #     except ConnectionError as e :
    #         eslogger.setLevel(esloggerlevel)
    #         raise e
    #     eslogger.setLevel(esloggerlevel)
    #
    #     if len(es_response.hits) > 0:
    #         first_hit = es_response.hits[0]
    #         if 'emma_titleId' in first_hit:
    #             return first_hit['emma_titleId']

    def truncate_publication_date(self, doc):
        if exists(doc, 'emma_publicationDate'):
            publication_date = doc['emma_publicationDate']
            parsed_date = iso8601.parse_date(publication_date)
            doc['emma_publicationDate'] = parsed_date.strftime("%Y-%m-%d")
