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
    print(sys.executable)
    print(sys.version)
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--bucket', dest='bucket', type=str, help='Bucket name')
    parser.add_argument('--key', dest='key', type=str, help='Key name')
    parser.add_argument('--debug', dest='debug', action='store_true', help='run in debug mode')
    parser.add_argument('--url', dest='opensearch_url', type=str, help='address of opensearch index')
    parser.add_argument('--index', dest='index_name', type=str, help='name of index to write to')
    parser.add_argument('--filename', dest='input_filename', type=str, help='filename to read instead of bucket')
    parser.add_argument('--tunnelhost', dest='tunnelhost', type=str, help='bastion host URL')
    parser.add_argument('--tunneluser', dest='tunneluser', type=str, help='bastion host username')
    parser.add_argument('--remote', dest='remoteurl', type=str, help='remote machine url')
    parser.add_argument('--sshkey', dest='sshkey', type=str, help='filename containing .pem file for bastion')
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
    
    session = boto3.Session()
    
    # tunnel_started = False 
    # if args.tunnelhost and args.remoteurl and args.tunneluser :
    #     # Setting up the SSH tunnel
    #     tunnel = SSHTunnelForwarder(
    #         (args.tunnelhost, 22),
    #         ssh_username=args.tunneluser,
    #         ssh_pkey=args.sshkey,
    #         remote_bind_address=(args.remoteurl, 443),
    #         local_bind_address=('localhost', 9200)
    #         )
    #     try:
    #         tunnel.start()
    #         logger.info("SSH tunnel established")
    #         tunnel_started = True
    #     except Exception as e:
    #         logger.info(f"Failed to establish SSH tunnel: {e}")


# Starting the SSH tunnel

    
    my_globals.opensearch_conn = OpenSearchConnection(opensearch_url, index, tunnelhost = tunnelhost, tunneluser = tunneluser, 
                                                      remoteurl = remoteurl, sshkey = sshkey)
    try : 
        my_globals.opensearch_conn.connect()
    
        if args.debug:
            logger.info('Debug mode activated')
            info = my_globals.opensearch_conn.connection.info()
            logger.info("Connected to OpenSearch")
            logger.info(info)

    
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
    
    finally:
        my_globals.opensearch_conn.close()

if __name__ == "__main__":
    main()

#
# end of file
#
