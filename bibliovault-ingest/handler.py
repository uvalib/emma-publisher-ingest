#
#
#

import os
import sys
import logging
import boto3
from shared import globals as my_globals
from shared.opensearch_connection import OpenSearchConnection
from process import process



lambda_opensearch_url = os.getenv("OPENSEARCH_URL", my_globals.DEFAULT_OPENSEARCH_HOST)

lambda_index = os.getenv("OPENSEARCH_INDEX", my_globals.DEFAULT_OPENSEARCH_INDEX)
        
lambda_tunnelhost = os.getenv("BASTION_HOST", None)
        
lambda_tunneluser = os.getenv("BASTION_USERNAME", None)
    
lambda_remoteurl = os.getenv("BASTION_REMOTE_HOST", None)
    
lambda_sshkey = os.getenv("BASTION_SSHKEY", None)

my_globals.botocore_session = boto3.Session()
    
my_globals.opensearch_conn = OpenSearchConnection(lambda_opensearch_url, lambda_index, tunnelhost = lambda_tunnelhost, tunneluser = lambda_tunneluser, 
                                                      remoteurl = lambda_remoteurl, sshkey = lambda_sshkey)



def lambda_handler(event, context):

    # return status
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if (my_globals.opensearch_conn.remotehost and my_globals.opensearch_conn.tunnelhost) :
        logger.info('sending records to opensearch at url '+ my_globals.opensearch_conn.remotehost)
        logger.info('  going through tunnel host at url '+ my_globals.opensearch_conn.tunnelhost)
        logger.info('  using local url of '+ my_globals.opensearch_conn.url)
        logger.info('  sending records to index '+ my_globals.opensearch_conn.index)
        
    else :
        logger.info('sending records directly to opensearch at url '+ my_globals.opensearch_conn.url)
        logger.info('  sending records to index '+ my_globals.opensearch_conn.index)
        
    ret = None

    if event:
        try : 
            my_globals.opensearch_conn.connect()
            logger.info( "RECV [" + str(event) + "]\n" )
    
            for record in event["Records"]:
                # extract the record and process
                body = eval(record["body"])
                val = process( body["bucket"], body["key"])
                if val:
                    ret = val

        finally:
            my_globals.opensearch_conn.close()

        return ret

#
# end of file
#
