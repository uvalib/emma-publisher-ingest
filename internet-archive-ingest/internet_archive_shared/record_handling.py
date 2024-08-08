import os
import json
import logging
import gzip

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry 

from internet_archive_shared import config, metadata
from datetime import datetime, timedelta
from shared import Dynamo
from shared import helpers 
from shared import globals as my_globals

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# only do these once
# EMMA_session = requests.Session()
# EMMA_retries = Retry(total=config.EMMA_INGESTION_RETRY, backoff_factor=0.2, status_forcelist=Retry.RETRY_AFTER_STATUS_CODES, 
#                      raise_on_status=False, respect_retry_after_header=True)
# EMMA_session.mount('https://', HTTPAdapter(max_retries=EMMA_retries))
IA_scrape_session = requests.Session()
IA_retries = Retry(total=config.IA_RETRY, backoff_factor=.2, status_forcelist=Retry.RETRY_AFTER_STATUS_CODES, raise_on_status=False)
IA_scrape_session.mount('https://', HTTPAdapter(max_retries=IA_retries))


def get_transform_send(ia_session, start_date = None, end_date = None):
    """
    Get records from IA
    Transform the records to EMMA format
    Send them to EMMA
    """
    if ( start_date is not None  and end_date is None):
        today = datetime.today()
        end_date = today.strftime("%Y-%m-%dT%H:%M:%SZ")
              
        my_globals.dynamo_table.set_db_value(Dynamo.BATCH_BOUNDARY_HEAD_TIMESTAMP, end_date)

    num_records = 0
    
    try:
        ia_response = get_next_scrape_response(Dynamo.SCAN_NEXT_TOKEN, config.SEARCH_PARAMS, start_date, end_date)
        if (ia_response.status_code == 200):
            logger.info("response received status code = 200")
            ia_json = ia_response.json()
            ia_records = null_safe_get_items(ia_json)
            logger.info("received json translated to objects")
            num_ia_records = len(ia_records)
            emma_records = metadata.transform_records(ia_records, ia_session, my_globals.doc_validator)
            num_records = len(emma_records)
            logger.info(str(num_ia_records) + " ia records transformed to "+ str(num_records) + " emma records")
            if len(emma_records) > 0:
                logger.info("Sending " + str(num_records) + " records to opensearch directly in batches.")
                if my_globals.upsert_handler != None : 
                    my_globals.upsert_handler.submit_in_batch(emma_records, config.EMMA_INGESTION_LIMIT)
                on_success(ia_json, ia_records)
            if is_diff_batch_complete(ia_json):
                my_globals.dynamo_table.set_db_value(Dynamo.SCAN_BATCH_COMPLETED, True)
                record_update_batch_boundary()
            my_globals.dynamo_table.update_counts(len(ia_records), num_records)
        else:
            logger.error("Internet Archive scrape API returned: " + str(ia_response.status_code))
            logger.error(ia_response.content)
    except ConnectionError as e:
        logger.exception("Connection error exiting")
        raise e
    except Exception as e:
        logger.exception("Transform and send failed. This set will be retried.")
        print("Exception:", e)
    return num_records


def on_success(oa_json, oa_records):
    """
    If the submission to EMMA ingestion is successful, update our records
    """
    last_record = oa_records[-1]
    first_record = oa_records[0]
    logger.info("First record in page dated " +
                str(first_record[config.DATE_BOUNDARY_FIELD]))
    logger.info("Last record scanned is now " +
                str(last_record['identifier']) + " last indexed " + str(last_record[config.DATE_BOUNDARY_FIELD]))
    if helpers.exists(oa_json, 'cursor'):
        cursor = oa_json['cursor']
        logger.info("Got cursor : " + str(cursor));
        my_globals.dynamo_table.set_db_value(Dynamo.SCAN_NEXT_TOKEN, cursor)
    else:
        logger.info("No cursor found");
        my_globals.dynamo_table.delete_db_value(Dynamo.SCAN_NEXT_TOKEN)

    if helpers.exists(last_record, config.DATE_BOUNDARY_FIELD):
        my_globals.dynamo_table.set_db_value(Dynamo.LAST_UPDATED_RECORD_TIMESTAMP, last_record[config.DATE_BOUNDARY_FIELD])
    else:
        logger.error("Possibly fatal error, no " +
                     config.DATE_BOUNDARY_FIELD + " in the last record.")

    my_globals.dynamo_table.set_db_value(Dynamo.LAST_UPDATED_RECORD_ID, last_record['identifier'])


def null_safe_get_items(ia_json):
    items = []
    if helpers.exists(ia_json, 'items'):
        items = ia_json['items']
    return items


def day_plus_one(date_str):
    # Parse the date string into a datetime object
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")

    # Add one day to the date object
    next_day = date_obj + timedelta(days=1)

    # Format the new date as a string
    next_day_str = next_day.strftime("%Y-%m-%d")
    return(next_day_str)


def build_query(start_date, end_date) :
    batch_boundary_date = start_date
    next_batch_boundary_date = end_date

    collection_list = config.IA_COLLECTION_LIST
    collection_clause = " OR ".join(collection_list)
    formats_list = list(filter(None, config.IA_FORMATS))

    query = "_exists_:" + config.DATE_BOUNDARY_FIELD + " AND collection:(" + collection_clause + ") AND mediatype:(texts)"

    if formats_list is not None and len(formats_list) > 0:
        formats = " AND ".join(formats_list)
        formats_clause = " AND format:(" + formats + ")"
        query = query + formats_clause
    
    if batch_boundary_date is None or len(batch_boundary_date) == 0:
        logger.info("No last batch boundary found, running to end of records")
        lower_limit = 'NULL'
    else:
        lower_limit = str(batch_boundary_date)

    if next_batch_boundary_date is None or len(next_batch_boundary_date) == 0:
        logger.error("No next batch boundary found, this is a fatal condition")
        upper_limit = 'NULL'
    else:
        upper_limit = str(next_batch_boundary_date)

    if lower_limit != 'NULL' or upper_limit != 'NULL':
        query = query + " AND " + config.DATE_BOUNDARY_FIELD + ":[" + lower_limit + " TO " + upper_limit + "]"

    return query


def get_next_scrape_response(next_token_name, params_to_copy, start_date, end_date):
    """
    Get the next page from the Internet Archive scrape API
    """
    query = build_query(start_date, end_date)
    next_page = my_globals.dynamo_table.get_db_value(next_token_name)

    params = params_to_copy.copy()
    params['q'] = query

    if next_page is not None:
        params['cursor'] = next_page

    logger.info("Scraping next page: " + json.dumps(params))

    ia_response = IA_scrape_session.post(
        config.IA_SCRAPE_URL,
        params=params,
        headers=config.HEADERS,
        timeout=config.IA_TIMEOUT)

    return ia_response


def record_set_batch_boundary(start_date, end_date):
    """
    Forcibly set the Internet Archive API date boundary for the current batch 
    """
    my_globals.dynamo_table.set_db_value(Dynamo.BATCH_BOUNDARY_TAIL_TIMESTAMP, start_date)
    my_globals.dynamo_table.set_db_value(Dynamo.BATCH_BOUNDARY_HEAD_TIMESTAMP, end_date)


def record_set_next_batch_boundary():
    """
    Save the Internet Archive API date boundary for the batch after the current one
    """
    start_date = my_globals.dynamo_table.get_db_value(Dynamo.BATCH_BOUNDARY_TAIL_TIMESTAMP)
    end_date = helpers.get_now_iso8601_datetime_utc()
    my_globals.dynamo_table.set_db_value(Dynamo.BATCH_BOUNDARY_HEAD_TIMESTAMP, end_date)
    return start_date, end_date


def record_update_batch_boundary():
    """
    When one batch is done, update the batch record boundary in the Dynamo DB database
    """
    boundary_date = my_globals.dynamo_table.get_db_value(Dynamo.BATCH_BOUNDARY_HEAD_TIMESTAMP)
    if boundary_date is not None:
        my_globals.dynamo_table.set_db_value(Dynamo.BATCH_BOUNDARY_TAIL_TIMESTAMP, boundary_date)
    my_globals.dynamo_table.delete_db_value(Dynamo.BATCH_BOUNDARY_HEAD_TIMESTAMP)
    # Reset query paging
    my_globals.dynamo_table.delete_db_value(Dynamo.SCAN_NEXT_TOKEN)


def is_diff_batch_complete(ia_response):
    """
    Check to see if the current batch is complete.  The current batch runs until it hits
    the previous record boundary, or until there are no more records.
    """
    return not helpers.exists(ia_response, 'cursor')


def get_last_updated_date_list(records):
    """
    Extracts the list of updated dates
    """
    return list(map(lambda x: x[config.DATE_BOUNDARY_FIELD], records))

