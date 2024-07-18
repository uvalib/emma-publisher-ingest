import os
import logging
from opensearchpy import OpenSearch, RequestsHttpConnection
from aws_requests_auth.aws_auth import AWSRequestsAuth
from requests.packages import urllib3
from requests.packages.urllib3.exceptions import InsecureRequestWarning

logger = logging.getLogger()
logger.setLevel(logging.INFO)

DEFAULT_OPENSEARCH_HOST = 'vpc-emma-index-production-glc53yq4angokfgqxlmzalupqe.us-east-1.es.amazonaws.com'
#DEFAULT_OPENSEARCH_HOST = 'emma-search-production.internal.lib.virginia.edu'
#DEFAULT_OPENSEARCH_HOST = 'localhost:9000'
DEFAULT_OPENSEARCH_INDEX = 'emma-federated-index-production'

EMMA_OPENSEARCH_REGION = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
EMMA_OPENSEARCH_SERVICE = 'es'

class OpenSearchConnection :

    
    def __init__(self, url, index, boto3 = None):
        self.url = url
        self.index = index
        self.EMMA_OPENSEARCH_URL_PARTS = url.partition(":")
        self.EMMA_OPENSEARCH_HOST = self.EMMA_OPENSEARCH_URL_PARTS[0]
        self.EMMA_OPENSEARCH_PORT = int(self.EMMA_OPENSEARCH_URL_PARTS[2]) if len(self.EMMA_OPENSEARCH_URL_PARTS[2]) > 0 else 443
        self.EMMA_PROXY =  self.EMMA_OPENSEARCH_HOST == 'localhost' 

        # if boto3 is not None : 
        #     credentials = boto3.Session().get_credentials()
        #     EMMA_ACCESS_KEY = credentials.access_key
        #     EMMA_SECRET_KEY = credentials.secret_key
        #
        # else :
        self.EMMA_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY_ID', None)
        self.EMMA_SECRET_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', None)

        self.auth = AWSRequestsAuth(aws_access_key=self.EMMA_ACCESS_KEY,
                               aws_secret_access_key=self.EMMA_SECRET_KEY,
                               aws_host=self.EMMA_OPENSEARCH_HOST,
                               aws_region=EMMA_OPENSEARCH_REGION,
                               aws_service=EMMA_OPENSEARCH_SERVICE)
        
        try :
            logger.info("trying to connect to host " + self.EMMA_OPENSEARCH_HOST + " at port " + str(self.EMMA_OPENSEARCH_PORT) )
            self.connection = OpenSearch(
                hosts=[{'host': self.EMMA_OPENSEARCH_HOST, 'port': self.EMMA_OPENSEARCH_PORT}],
                http_auth=self.auth if not self.EMMA_PROXY else None,
                use_ssl= True,
                verify_certs= not self.EMMA_PROXY,
                connection_class=RequestsHttpConnection,
                # don't show warnings about ssl certs verification
                ssl_show_warn=False)
        except Exception as e :
            logger.exception(e)
            
            


# def make_opensearch_connection(host, index ) :
#     global EMMA_ELASTICSEARCH_HOST
#     global EMMA_ELASTICSEARCH_INDEX
#     global ELASTICSEARCH_CONN
#     EMMA_ELASTICSEARCH_HOST = host
#     EMMA_ELASTICSEARCH_INDEX = index
#     EMMA_ELASTICSEARCH_REGION = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
#     EMMA_ELASTICSEARCH_SERVICE = 'es'
#
#     GOLDEN_KEY = os.environ.get('GOLDEN_KEY', 'unset')
#
#     #credentials = boto3.Session().get_credentials()
#     service = 'es'
#     #credentials = boto3.Session().get_credentials()
#     #awsauth = AWSV4SignerAuth(EMMA_ACCESS_KEY, EMMA_SECRET_KEY, EMMA_ELASTICSEARCH_REGION, EMMA_ELASTICSEARCH_SERVICE)
#
#     auth = AWSRequestsAuth(aws_access_key=EMMA_ACCESS_KEY,
#                            aws_secret_access_key=EMMA_SECRET_KEY,
#                            aws_host=EMMA_ELASTICSEARCH_HOST,
#                            aws_region=EMMA_ELASTICSEARCH_REGION,
#                            aws_service=EMMA_ELASTICSEARCH_SERVICE)
# # awsauth = AWSV4SignerAuth(credentials.access_key, credentials.secret_key,
# #                    EMMA_ELASTICSEARCH_REGION, EMMA_ELASTICSEARCH_SERVICE, session_token=credentials.token)
#
# # ELASTICSEARCH_CONN = Elasticsearch(
# #     hosts=[{'host': EMMA_ELASTICSEARCH_HOST, 'port': 443}],
# #     http_auth=awsauth,
# #     use_ssl=True,
# #     verify_certs=True,
# #     connection_class=RequestsHttpConnection
# # )
#
#     EMMA_ELASTICSEARCH_URL_PARTS = EMMA_ELASTICSEARCH_HOST.partition(":")
#     EMMA_ELASTICSEARCH_PORT = int(EMMA_ELASTICSEARCH_URL_PARTS[2]) if len(EMMA_ELASTICSEARCH_URL_PARTS[2]) > 0 else 443
#     EMMA_PROXY =  EMMA_ELASTICSEARCH_URL_PARTS[0] == 'localhost' 
#
#     if (EMMA_PROXY) :
#         urllib3.disable_warnings(InsecureRequestWarning)
#
#     ELASTICSEARCH_CONN = OpenSearch(
#         hosts=[{'host': EMMA_ELASTICSEARCH_URL_PARTS[0], 'port': EMMA_ELASTICSEARCH_PORT}],
#         # http_auth=auth,
#         use_ssl= True,
#         verify_certs= not EMMA_PROXY,
#         connection_class=RequestsHttpConnection,
#         # don't show warnings about ssl certs verification
#         ssl_show_warn=False
#     )
#     return ELASTICSEARCH_CONN
#
#
# RENAMED_FIELDS = {
#     'emma_lastRemediationNote':'rem_comments',
#     'emma_lastRemediationDate': 'rem_remediationDate',
#     'emma_repositoryMetadataUpdateDate': 'emma_repositoryUpdateDate'
# }
#
# ORIGINAL_FIELDS = {
#     'rem_comments':'emma_lastRemediationNote',
#     'rem_remediationDate': 'emma_lastRemediationDate',
#     'emma_repositoryUpdateDate': 'emma_repositoryMetadataUpdateDate'
# }