#
#
#
import os
import logging
import boto3
import sys
import argparse
from shared import globals as my_globals
from shared.opensearch_connection import OpenSearchConnection
from handler import *
from process import *


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bucket', dest='bucket', type=str, help='Bucket name')
    parser.add_argument('--key', dest='key', type=str, help='Key name')
    parser.add_argument('--debug', dest='debug', action='store_true', help='run in debug mode')
    parser.add_argument('--url', dest='opensearch_url', type=str, help='address of opensearch index')
    parser.add_argument('--index', dest='index_name', type=str, help='name of index to write to')
    parser.add_argument('--filename', dest='input_filename', type=str, help='filename to read instead of bucket')
    args = parser.parse_args()

    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

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
        
    if opensearch_url:
        my_globals.opensearch_conn = OpenSearchConnection(opensearch_url, index)

    if args.debug:
        logger.info('Debug mode activated')

    if args.bucket :    
        # payload is an array of records containing the body sent to the queue
        body = {
            "bucket": args.bucket,
            "key": args.key,
            }
        payload = {
            "Records": [
                { "body": str(body) }
            ]
        }
        # process
        err = lambda_handler(payload, None)
        
    elif args.input_filename : 
        err = readfile(args.input_filename)



if __name__ == "__main__":
    main()

#
# end of file
#
