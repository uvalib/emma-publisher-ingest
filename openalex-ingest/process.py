#
#
#

import logging
import signal
import gzip
import time
from shared import helpers
from shared import Dynamo
from shared import globals as my_globals
from openalex_shared import config, record_handling
from shared.UpsertHandler import UpsertHandler

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Signal handler function
def signal_handler(sig, frame):
    print("Received signal {}. Setting termination flag...".format(sig))
    my_globals.terminate_flag = True

def run(start_date = None, end_date = None):
    """
    This is the main loop that makes several calls to extract, transform, and load data from
    Internet Archive into the federated index.
    It is separated out from the top-level lambda function so that the session and Dynamo DB
    can be easily mocked for testing.
    """
    # Register signal handler for SIGINT (Ctrl+C)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Starting OpenAlex to EMMA transfer service PST " + helpers.get_today_iso8601_datetime_pst())
        
    running = my_globals.dynamo_table.check_running(Dynamo.SCAN_RUNNING, my_globals.debug)
    if running:
        logger.info("Full scan already running")
        return
    
    if (start_date is not None):
        logger.info("Forcing new batch from date: " + str(start_date))
        if (end_date is None) :
            end_date = helpers.get_now_iso8601_datetime_utc()
        record_handling.record_set_batch_boundary(start_date, end_date)
        my_globals.dynamo_table.delete_db_value(Dynamo.SCAN_NEXT_TOKEN)
        my_globals.dynamo_table.set_db_value(Dynamo.SCAN_BATCH_COMPLETED, False)
    else:
        completed = my_globals.dynamo_table.check_batch_completed(Dynamo.SCAN_BATCH_COMPLETED)
        if completed:
            logger.info("Starting new batch")
            start_date, end_date = record_handling.record_set_next_batch_boundary()
            my_globals.dynamo_table.set_db_value(Dynamo.SCAN_BATCH_COMPLETED, False)
        else:
            start_date = my_globals.dynamo_table.get_db_value(Dynamo.BATCH_BOUNDARY_TAIL_TIMESTAMP)
            end_date = my_globals.dynamo_table.get_db_value(Dynamo.BATCH_BOUNDARY_HEAD_TIMESTAMP)

    my_globals.dynamo_table.start_running(Dynamo.SCAN_RUNNING)

    logger.info('Start Running')

    records_sent = 0
    completed = False
    
    my_globals.upsert_handler = UpsertHandler(my_globals.opensearch_conn)
    total_time = 0.0
    iterations = 0
    if (my_globals.lambda_context != None) :
        # Get remaining time in milliseconds
        remaining_time = my_globals.lambda_context.get_remaining_time_in_millis()

        # Convert to seconds
        remaining_seconds = remaining_time / 1000.0
        logger.info(f"Time remaining in lambda (in seconds): {remaining_seconds}")

    try: 
        for i in range(1, config.OA_RETRIEVALS + 1):
            batchstart = time.time()
            num_in_chunk = record_handling.get_transform_send(start_date, end_date)
            records_sent = records_sent + num_in_chunk
            batchend = time.time()
            elapsed_time = batchend - batchstart
            total_time += elapsed_time
            iterations += 1
            logger.info("Finished batch " + str(i) + ", total loaded so far: " + str(records_sent))
            logger.info(f"  Elapsed for batch time: {elapsed_time:.4f} seconds")
            if (my_globals.lambda_context != None) :
                # Get remaining time in milliseconds
                remaining_time = my_globals.lambda_context.get_remaining_time_in_millis()
    
                # Convert to seconds
                remaining_seconds = remaining_time / 1000.0
                logger.info(f"Time remaining in lambda (in seconds): {remaining_seconds}")
                average_loop_time = (total_time / iterations)
                if (remaining_seconds < 2 * average_loop_time):
                    my_globals.terminate_flag = True
                    logger.info("Running out of time, setting terminate flag")
            completed = my_globals.dynamo_table.get_db_value(Dynamo.SCAN_BATCH_COMPLETED)
            if (completed):
                logger.info("Current batch completed")
                break
            if (my_globals.terminate_flag ):
                logger.info("Terminate flag set, exiting cleanly")
                break
            
        ia_pulled = my_globals.dynamo_table.get_db_value(Dynamo.SCAN_RUNNING_TOTAL_SOURCE)
        emma_loaded = my_globals.dynamo_table.get_db_value(Dynamo.SCAN_RUNNING_TOTAL_FEDERATED)
        logger.info("Running total: " + str(ia_pulled) + " pulled from  "+ config.OA_REPOSITORY_NAME + " " + str(emma_loaded) + " loaded to federated index.")
    
    except Exception as e:
        logger.exception(e)
        raise e
    
    finally : 
        my_globals.dynamo_table.end_running(Dynamo.SCAN_RUNNING)
        return records_sent, completed

def readfile(filename):
    """
    This is the main loop receives a filename (or url) containing bibliovault metadata
    It reads the data, processes it and sends it to the opensearch index.
    It is separated out from the top-level lambda function the processing can also be started from the command line
    """
    
    logger.info("Starting BiblioVault to EMMA transfer service PST " + helpers.get_today_iso8601_datetime_pst())
        
    logger.info('Start Running')

    records_sent = 0
    
    # Read the contents of the file or url into file_contents          
    # if (filename.startswith('http://') or filename.startswith('https://')):
    #     # if ("s3.amazonaws.com" in filename) :
    #     #     filename = get_presigned_url_from_url(filename)
    #     response = requests.get(filename)
    #     # Raise an exception if the request was unsuccessful
    #     response.raise_for_status()
    #     # Use the content of the response as you would with a file
    #     file_contents = response.content.decode('utf-8')  # assuming the file is in UTF-8 encoding
    # else:
    if filename.endswith('.gz'):
        my_open = gzip.open
    else:
        my_open = open    

    my_globals.upsert_handler = UpsertHandler(my_globals.opensearch_conn)
    
    with my_open(filename, "r", encoding='utf-8') as file:

        try : 
            # Read the contents of the file            
    
            cnt = record_handling.process_file(file)
    
            records_sent += cnt
            logger.info("Finished load of file "+ filename + ", total loaded " + str(records_sent))
        except Exception  as e:
            logger.exception()
            raise e
        finally : 
            oa_pulled = my_globals.dynamo_table.get_db_value(Dynamo.SCAN_RUNNING_TOTAL_SOURCE)
            emma_loaded = my_globals.dynamo_table.get_db_value(Dynamo.SCAN_RUNNING_TOTAL_FEDERATED)
            logger.info("Running total: " + str(oa_pulled) + " pulled from  "+ config.OA_REPOSITORY_NAME + " " + str(emma_loaded) + " loaded to federated index.")
            my_globals.dynamo_table.end_running(Dynamo.SCAN_RUNNING)
            return records_sent, True

#
# end of file
#
