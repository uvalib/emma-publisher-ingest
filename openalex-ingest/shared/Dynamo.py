from datetime import datetime, timedelta
from shared import helpers

import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SCAN_BATCH_COMPLETED = 'SCAN_BATCH_COMPLETED'
VERIFY_BATCH_COMPLETED = 'VERIFY_BATCH_COMPLETED'
BATCH_BOUNDARY_TAIL_TIMESTAMP = 'BATCH_BOUNDARY_TAIL_TIMESTAMP'
BATCH_BOUNDARY_HEAD_TIMESTAMP = 'BATCH_BOUNDARY_HEAD_TIMESTAMP'
LAST_UPDATED_RECORD_ID = 'LAST_UPDATED_RECORD_ID'
LAST_VERIFIED_RECORD_ID = 'LAST_VERIFIED_RECORD_ID'
LAST_UPDATED_RECORD_TIMESTAMP = 'LAST_UPDATED_RECORD_TIMESTAMP'
SCAN_RUNNING = 'SCAN_RUNNING'
VERIFY_RUNNING = 'VERIFY_RUNNING'
VERIFY_NEXT_TOKEN = 'VERIFY_NEXT_TOKEN'
SCAN_NEXT_TOKEN = 'SCAN_NEXT_TOKEN'
SCAN_RUNNING_TOTAL_SOURCE = 'SCAN_RUNNING_TOTAL_SOURCE'
SCAN_RUNNING_TOTAL_FEDERATED = 'SCAN_RUNNING_TOTAL_FEDERATED'
VERIFY_RUNNING_TOTAL_SOURCE = 'VERIFY_RUNNING_TOTAL_SOURCE'
VERIFY_RUNNING_TOTAL_FEDERATED = 'VERIFY_RUNNING_TOTAL_FEDERATED'
INTERVAL_IN_MIN = 5

class DynamoTable :
    def __init__(self, dynamodb, table_name, prefix):
        self.dynamodb = dynamodb
        self.prefix = prefix
        self.table = dynamodb.Table(table_name)

    def initialize_db_flag(self, flag_name, init):
        field = self.prefix + flag_name
        try :
            self.table.put_item(
                Item={
                    'name': field,
                    'val': init
                }
            )
        except ResourceNotFoundException as e:
            logger.error("put_item failed for field: "+ field + " on table: " + table_name)
            raise e


    def get_db_value(self, attr_name):
        field = self.prefix + attr_name
        try: 
            response = self.table.get_item(
                Key={
                    'name': field
                })
        except ResourceNotFoundException as e:
            logger.error("get_item failed for field: "+ field + " on table: " + table_name)
            raise e

        if 'Item' in response and len(response['Item']) > 0:
            item = response['Item']
            return item['val']
        else:
            return 


    def set_db_value(self, attr_name, attr_value):
        field = self.prefix + attr_name
        try :
            self.table.put_item(
                Item={
                    'name': field,
                    'val': attr_value
                }
            )
        except ResourceNotFoundException as e:
            logger.error("put_item failed for field: "+ field + " on table: " + table_name)
            raise e


    def delete_db_value(self, attr_name):
        field = self.prefix + attr_name
        try :
            self.table.delete_item(
                Key={
                    'name': field
                }
            )
        except ResourceNotFoundException as e:
            logger.error("delete_item failed for field: "+ field + " on table: " + table_name)
            raise e
    


    def start_running(self, flag_name):
        field = self.prefix + flag_name
        try :
            self.table.update_item(
                Key={
                    'name': field
                },
                UpdateExpression='SET val = :val1, started = :val2',
                ExpressionAttributeValues={
                    ':val1': True,
                    ':val2': helpers.get_today_iso8601_datetime_pst()
                }
            )
        except ResourceNotFoundException as e:
            logger.error("update_item failed for field: "+ field + " on table: " + table_name)
            raise e


    def end_running(self, flag_name):
        field = self.prefix + flag_name
        try:
            self.table.update_item(        
                Key={
                    'name': field
                },
                UpdateExpression='SET val = :val1',
                ExpressionAttributeValues={
                    ':val1': False
                }
            )
            self.table.update_item(
                Key={
                    'name': field
                },
                UpdateExpression='REMOVE started'
            )
        except ResourceNotFoundException as e:
            logger.error("update_item failed for field: "+ field + " on table: " + table_name)
            raise e


    def check_running(self, flag_name, debug):
        """
        Check to see if the job is already running.
        If the job is running but started more than 15 minutes ago, we can mark it done because lambda functions are limited to 15 minutes.
    
        """
        running = False
        if (debug == False) : 
            field = self.prefix + flag_name
            try: 
                response = self.table.get_item(
                    Key={
                        'name': field
                    })
            except ResourceNotFoundException as e:
                logger.error("get_item failed for field: "+ field + " on table: " + table_name)
                raise e
                
            if 'Item' in response and len(response['Item']) > 0:
                item = response['Item']
                running = item['val']
                if running:
                    if 'started' in item:
                        started = datetime.fromisoformat(item['started'])
                        logger.info("Current run started " + str(started))
                        now = helpers.get_now_datetime_pst()
                        logger.info("Current time is     " + str(now))
                        # If it's been running more than 15 minutes we can mark it done
                        minutes_ago = (now - started) // timedelta(minutes=1)
                        logger.info('Minutes elapsed: ' + str(minutes_ago))
                        if minutes_ago > INTERVAL_IN_MIN:
                            logger.info("Marking old job done.")
                            self.end_running(flag_name)
                            running = False
                   
            else:
                self.initialize_db_flag(flag_name, False)
        
        return running


    def check_batch_completed(self, flag_name):
        completed = True
        stored_value = self.get_db_value(flag_name)
        if stored_value is not None:
            completed = stored_value
        else:
            self.initialize_db_flag(flag_name, True)
    
        return completed


    def update_counts(self, source_records, fed_records):
        """
        Update our count of records processed in the Dynamo DB table.
        """
        previous_source_records = self.get_db_value(SCAN_RUNNING_TOTAL_SOURCE)
        previous_fed_records = self.get_db_value(SCAN_RUNNING_TOTAL_FEDERATED)
    
        if previous_source_records is None:
            previous_source_records = 0
        if previous_fed_records is None:
            previous_fed_records = 0
        source_records = source_records + previous_source_records
        fed_records = fed_records + previous_fed_records
        self.set_db_value(SCAN_RUNNING_TOTAL_SOURCE, source_records)
        self.set_db_value(SCAN_RUNNING_TOTAL_FEDERATED, fed_records)
    