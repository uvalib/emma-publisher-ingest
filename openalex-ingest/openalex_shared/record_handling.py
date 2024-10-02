import re
import json
import logging
import requests
from requests.adapters import HTTPAdapter
from datetime import datetime, timedelta
from shared import globals as my_globals

from urllib3 import Retry 

from openalex_shared import config, metadata
from shared import helpers
from shared import Dynamo
from shared.helpers import get_now_iso8601_datetime_utc

logger = logging.getLogger()
logger.setLevel(logging.INFO)

OA_session = requests.Session()
OA_retries = Retry(total=config.OA_RETRY, backoff_factor=.2, status_forcelist=Retry.RETRY_AFTER_STATUS_CODES, raise_on_status=False)
OA_session.mount('https://', HTTPAdapter(max_retries=OA_retries))

def get_transform_send(start_date = None, end_date = None):
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
        oa_response = get_next_scrape_response(Dynamo.SCAN_NEXT_TOKEN, config.SEARCH_PARAMS, start_date, end_date)
        if (oa_response.status_code == 200):
            logger.info("response received status code = 200")
            # content = oa_response.content
            oa_json = oa_response.json()
            oa_records = null_safe_get_results(oa_json)
            logger.info("received json translated to objects")
            if helpers.exists(oa_json, 'meta') and helpers.exists(oa_json['meta'], 'count'):
                logger.info("count of documents that match: "+ str(oa_json['meta']['count']))
            num_oa_records = len(oa_records)
            emma_records = metadata.transform_records(oa_records, my_globals.doc_validator)
            num_records = len(emma_records)
            logger.info(str(num_oa_records) + " oa records transformed to "+ str(num_records) + " emma records")
            if len(emma_records) > 0:
                logger.info("Sending " + str(num_records) + " records to opensearch directly in batches.")
                if my_globals.upsert_handler != None : 
                    my_globals.upsert_handler.submit_in_batch(emma_records, config.EMMA_INGESTION_LIMIT)
                on_success(oa_json, oa_records)
            if is_diff_batch_complete(oa_json):
                my_globals.dynamo_table.set_db_value(Dynamo.SCAN_BATCH_COMPLETED, True)
                record_update_batch_boundary()
            my_globals.dynamo_table.update_counts(len(oa_records), num_records)
        else:
            logger.error("OpenAlex scrape API returned: " + str(oa_response.status_code))
            logger.error(oa_response.content)
    except ConnectionError as e:
        logger.exception("Connection error exiting")
        raise e
    except Exception as e:
        logger.exception("Transform and send failed. This set will be retried.")
        print("Exception:", e)
    return num_records

def process_file(file):
    """
    Get records from IA
    Transform the records to EMMA format
    Send them to EMMA
    """
    pattern = r'("apc_list": {"value": 0,)|("is_oa": true)'
    pattern2 = r'type": "article"'
    emma_records = []
    num_read = 0
    num_records = 0

    try:
        line = file.readline()
        while (line) :
            num_read += 1
            is_openaccess = re.search(pattern, line)
            is_article = re.search(pattern2, line)
            if (is_article and is_openaccess) :
                oa_record = json.loads(line)
                emma_record = metadata.transform_records([oa_record], my_globals.doc_validator)
                emma_records.extend(emma_record)
                if (len(emma_records) == config.EMMA_INGESTION_LIMIT_FROM_FILE):
                    if my_globals.upsert_handler != None : 
                        my_globals.upsert_handler.submit_in_batch(emma_records, config.EMMA_INGESTION_LIMIT_FROM_FILE)
                    num_records += len(emma_records)
                    emma_records = []
            line = file.readline()
        if (len(emma_records) > 0) :
            if my_globals.upsert_handler != None : 
                my_globals.upsert_handler.submit_in_batch(emma_records, config.EMMA_INGESTION_LIMIT_FROM_FILE)
            num_records += len(emma_records)

            my_globals.dynamo_table.update_counts(num_read, num_records)
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
                str(first_record[config.DATE_UPDATED_FIELD]))
    logger.info("Last record scanned is now " +
                str(last_record['id']) + " last indexed " + str(last_record[config.DATE_UPDATED_FIELD]))
    if helpers.exists(oa_json, 'meta') and helpers.exists(oa_json['meta'], 'next_cursor'):
        my_globals.dynamo_table.set_db_value(Dynamo.SCAN_NEXT_TOKEN, oa_json['meta']['next_cursor'])
    else:
        my_globals.dynamo_table.delete_db_value(Dynamo.SCAN_NEXT_TOKEN)

    if helpers.exists(last_record, config.DATE_UPDATED_FIELD):
        my_globals.dynamo_table.set_db_value(Dynamo.LAST_UPDATED_RECORD_TIMESTAMP, last_record[config.DATE_UPDATED_FIELD])
    else:
        logger.error("Possibly fatal error, no " +
                     config.DATE_UPDATED_FIELD + " in the last record.")

    my_globals.dynamo_table.set_db_value(Dynamo.LAST_UPDATED_RECORD_ID, last_record['id'])


def null_safe_get_results(ia_json):
    items = []
    if helpers.exists(ia_json, 'results'):
        items = ia_json['results']
    return items

def day_plus_one(date_str):
    # Parse the date string into a datetime object
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")

    # Add one day to the date object
    next_day = date_obj + timedelta(days=1)

    # Format the new date as a string
    next_day_str = next_day.strftime("%Y-%m-%d")
    return(next_day_str)

def build_query(start_date, end_date):
    batch_boundary_date = start_date
    next_batch_boundary_date = end_date

    query = "*"
    filterval = ""

    if batch_boundary_date is None or len(batch_boundary_date) == 0:
        logger.error("No last batch boundary date found, this is a fatal condition")
        lower_limit = 'NULL'
        raise RuntimeError("No start date specified, and no previous run-end date found")
    else:
        lower_limit = str(batch_boundary_date)
        lower_limit_date = str(batch_boundary_date)[:10]

    if next_batch_boundary_date is None or len(next_batch_boundary_date) == 0:
        logger.info("No next batch boundary date found, running to end of records")
        upper_limit = 'NULL'
    else:
        upper_limit = str(next_batch_boundary_date)

    if lower_limit != 'NULL' and upper_limit != 'NULL' and config.DATE_UPPER_BOUNDARY_FIELD != 'NULL' :
        filterval =  config.DATE_LOWER_BOUNDARY_FIELD + ":" + lower_limit + "," +config.DATE_UPPER_BOUNDARY_FIELD + ":" +  upper_limit + "," + config.DATE_LOWER_BOUNDARY_DATE_FIELD + ":" + lower_limit_date
    elif lower_limit != 'NULL' and ( upper_limit == 'NULL' or config.DATE_UPPER_BOUNDARY_FIELD == 'NULL' ) :
        filterval =  config.DATE_LOWER_BOUNDARY_DATE_FIELD + ":" + lower_limit_date
    return query, filterval


def get_next_scrape_response(next_token_name, params_to_copy, start_date, end_date):
    """
    Get the next page from the OpenAlex scrape API
    """
    query, filterval = build_query(start_date, end_date)
    next_page = my_globals.dynamo_table.get_db_value(next_token_name)

    params = params_to_copy.copy()
    if (filterval != ""):
        params['filter'] = params['filter'] + "," + filterval
    params['q'] = query
    
    # add this header to be in the polite pool
    headers = {'mailto': 'rwl@virginia.edu',
               'api_key': '4kWwJ3rcfsrMauDJcrcaC5' }
    
    if next_page is not None:
        params['cursor'] = next_page
    else :
        params['cursor'] = '*'
        
    logger.info("Scraping next page: " + json.dumps(params))

    oa_response = OA_session.get(
        config.OA_SCRAPE_URL,
        params=params,
        headers=headers,
        timeout=config.OA_TIMEOUT)

    return oa_response

# def record_set_next_batch_boundary(start_date, end_date=None):
#     """
#     Save the OpenAlex API date boundary for the batch after the current one
#     """
#     my_globals.dynamo_table.set_db_value(Dynamo.BATCH_BOUNDARY_TAIL_TIMESTAMP, start_date)
#     if (end_date is None  and  config.DATE_UPPER_BOUNDARY_FIELD == "NULL"):
#         today = datetime.today()
#         end_date = today.strftime("%Y-%m-%d")
#     else:
#         end_date = day_plus_one(start_date)    
#     my_globals.dynamo_table.set_db_value(Dynamo.BATCH_BOUNDARY_HEAD_TIMESTAMP, end_date)

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


def is_diff_batch_complete(oa_response):
    """
    Check to see if the current batch is complete.  The current batch runs until it hits
    the previous record boundary, or until there are no more records.
    """
    return not (helpers.exists(oa_response, 'meta') and helpers.exists(oa_response['meta'], 'next_cursor'))

