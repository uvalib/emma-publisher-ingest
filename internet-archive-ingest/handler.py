#
#
#

import os
import sys
import logging
import boto3
from shared import globals as my_globals
from shared.OpenSearchConnection import OpenSearchConnection
from process import run
from internet_archive_shared import config
from internetarchive import get_session



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

    try : 
        my_globals.opensearch_conn.connect()

        ia_session = get_session(config=config.IA_SESSION_CONFIG)

        num, completed = run(ia_session)

        if ( num > 0 and completed):
            # all is well
            ret = { 'num_processed': str(num),
                    'completed' : str(completed) }
        else :
            ret = { 'num_processed': str(num),
                    'completed' : str(completed) }

    except Exception  as e:
        logger.exception()
        ret = { 'exception': str(e) }

    finally:
        my_globals.opensearch_conn.close()

    return ret

#
# end of file
#
