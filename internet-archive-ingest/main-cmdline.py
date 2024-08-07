#
#
#
import os
import logging
import boto3
import sys
import argparse

from shared import globals as my_globals
from shared.Dynamo import DynamoTable
from shared.OpenSearchConnection import OpenSearchConnection
from handler import *
from process import *
from internetarchive import get_session

def main():
    print(sys.executable)
    print(sys.version)
    
    parser = argparse.ArgumentParser()
    # parser.add_argument('--bucket', dest='bucket', type=str, help='Bucket name')
    # parser.add_argument('--key', dest='key', type=str, help='Key name')
    parser.add_argument('--debug', dest='debug', action='store_true', help='run in debug mode')
    parser.add_argument('--local', dest='local_db', action='store_true', help='use dynamodb on localhost')
    parser.add_argument('--url', dest='opensearch_url', type=str, help='address of opensearch index')
    parser.add_argument('--index', dest='index_name', type=str, help='name of index to write to')
    parser.add_argument('--filename', dest='input_filename', type=str, help='filename to read instead of bucket')
    parser.add_argument('--tunnelhost', dest='tunnelhost', type=str, help='bastion host URL')
    parser.add_argument('--tunneluser', dest='tunneluser', type=str, help='bastion host username')
    parser.add_argument('--remote', dest='remoteurl', type=str, help='remote machine url')
    parser.add_argument('--sshkey', dest='sshkey', type=str, help='filename containing .pem file for bastion')
    parser.add_argument('-s', '--startdate', dest='start_date', help='start date for use with API')
    parser.add_argument('-e', '--enddate', dest='end_date', help='end date for use with API')

    args = parser.parse_args()

    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    my_globals.botocore_session = boto3.Session()
    if args.local_db :
        dynamo_url="http://localhost:8000"
        db = my_globals.botocore_session.resource('dynamodb', endpoint_url=dynamo_url)
        my_globals.dynamo_table = DynamoTable(db, config.DYNAMODB_LOADER_TABLE, config.STATUS_TABLE_PREFIX)
        logger.info("Using Dynamo db table : " + config.STATUS_TABLE_PREFIX + config.DYNAMODB_LOADER_TABLE + " for local database at " + dynamo_url)
    else :
        region_name="us-east-1"
        db = my_globals.botocore_session.resource('dynamodb', region_name=region_name)
        my_globals.dynamo_table = DynamoTable(db, config.DYNAMODB_LOADER_TABLE, config.STATUS_TABLE_PREFIX)
        logger.info("Using Dynamo db table : " + config.STATUS_TABLE_PREFIX + config.DYNAMODB_LOADER_TABLE + " for database in region " + region_name)

    if args.opensearch_url:
        logger.info('sending records directly to opensearch at url '+args.opensearch_url)
        opensearch_url = args.opensearch_url
    else :
        opensearch_url = os.getenv("OPENSEARCH_URL", my_globals.DEFAULT_OPENSEARCH_HOST)
        logger.info('sending records directly to opensearch at url '+opensearch_url)

    if args.index_name:
        logger.info('sending records directly to opensearch index '+args.index_name)
        index = args.index_name
    else : 
        index = os.getenv("OPENSEARCH_INDEX", my_globals.DEFAULT_OPENSEARCH_INDEX)
        logger.info('sending records directly to opensearch index '+index)
        
    if args.tunnelhost :
        tunnelhost = args.tunnelhost
    else :
        tunnelhost = os.getenv("BASTION_HOST", None)
        
    if args.tunneluser :
        tunneluser = args.tunneluser
    else :
        tunneluser = os.getenv("BASTION_USERNAME", None)
    
    if args.remoteurl :
        remoteurl = args.remoteurl
    else :
        remoteurl = os.getenv("BASTION_REMOTE_HOST", None)
    
    if args.sshkey :
        sshkey = args.sshkey
    else :
        sshkey = os.getenv("BASTION_SSHKEY", None)
        
    my_globals.opensearch_conn = OpenSearchConnection(opensearch_url, index, tunnelhost = tunnelhost, tunneluser = tunneluser, 
                                                      remoteurl = remoteurl, sshkey = sshkey)
    try : 
        my_globals.opensearch_conn.connect()
    
        if args.debug:
            my_globals.debug = True
            logger.info('Debug mode activated')
            info = my_globals.opensearch_conn.connection.info()
            logger.info("Connected to OpenSearch")
            logger.info(info)

        ia_session = get_session(config=config.IA_SESSION_CONFIG)
   
        num, completed = run(ia_session, start_date = args.start_date, end_date = args.end_date)
        if ( num > 0 and completed):
            # all is well
            ret = None
        else :
            ret = { 'num_processed': str(num),
                    'completed' : str(completed) }
   
    except Exception  as e:
        logger.exception(str(e))
        ret = { 'exception': str(e) }
    
    finally: 
        my_globals.opensearch_conn.close()
        sys.exit(ret)
        
if __name__ == "__main__":
    main()

#
# end of file
#
