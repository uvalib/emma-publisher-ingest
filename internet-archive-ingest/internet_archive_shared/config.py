# import logging
import os

IA_SECRET_KEY = os.environ.get('IA_SECRET_KEY', 'Missing')
IA_ACCESS_KEY = os.environ.get('IA_ACCESS_KEY', 'Missing')
IA_SITE = os.environ.get('IA_SITE', 'internetArchive')
IA_REPOSITORY_NAME = os.environ.get('IA_REPOSITORY_NAME','internetArchive')
IA_SESSION_CONFIG = {'s3': {'access': IA_ACCESS_KEY, 'secret': IA_SECRET_KEY}}
IA_SCRAPE_URL = 'https://archive.org/services/search/v1/scrape'
IA_PERSONALIZE = os.environ.get('IA_PERSONALIZE','')


IA_COLLECTION_LIST = os.environ.get('IA_COLLECTION_LIST', 'internetarchivebooks').split(",")
IA_FORMATS = os.environ.get('IA_FORMATS', 'PDF,(MARC Binary)').split(",")

EMMA_INGESTION_LIMIT = int(os.environ.get('EMMA_INGESTION_LIMIT', 200))
EMMA_INGESTION_LIMIT = int(os.environ.get('EMMA_INGESTION_LIMIT', 100))
EMMA_INGESTION_RETRY = int(os.environ.get('EMMA_INGESTION_RETRY', 2))
EMMA_INGESTION_TIMEOUT = int(os.environ.get('EMMA_INGESTION_TIMEOUT', 15))
EMMA_COMPRESS_OUTGOING = bool(os.environ.get('EMMA_COMPRESS_OUTGOING', True))

IA_RETRY = int(os.environ.get('IA_RETRY', 2))
IA_RETRIEVALS = int(os.environ.get('IA_RETRIEVALS', 500))
IA_TIMEOUT = int(os.environ.get('IA_TIMEOUT', 120))
IA_PAGE_SIZE = int(os.environ.get('IA_PAGE_SIZE', 5000))

STATUS_TABLE_PREFIX = os.environ.get('EMMA_STATUS_TABLE_PREFIX', 'IA_')
DYNAMODB_LOADER_TABLE = os.environ.get('EMMA_STATUS_TABLE_NAME', 'emma_bookshare_loader')        


DATE_BOUNDARY_FIELD = 'indexdate'

SEARCH_FIELDS = ['collection',
                 'creator',
                 'date',
                 'description',
                 'external-identifier',
                 'format',
                 'isbn',
                 'identifier',
                 'indexdate',
                 'language',
                 'lccn',
                 'licenseurl',
                 'mediatype',
                 'name',
                 'oclc',
                 'publisher',
                 'related-external-id',
                 'rights',
                 'subject',
                 'title',
                 'type',
                 'year'
                 ]

VERIFY_FIELDS = ['identifier']

SEARCH_PARAMS = {'count': IA_PAGE_SIZE,
                 # Causes IA error: "userid xxxxxxx is not authorized to access .", errorType: "unknown"
                 # 'scope': 'all'
                 'fields' : ','.join(SEARCH_FIELDS),
                 'personalize': IA_PERSONALIZE}

VERIFY_SEARCH_PARAMS = {'count': IA_PAGE_SIZE,
                 # Causes IA error: "userid xxxxxxx is not authorized to access .", errorType: "unknown"
                 # 'scope': 'all'
                 'fields' : ','.join(VERIFY_FIELDS),
                 'personalize': IA_PERSONALIZE}

HEADERS = {
    'Authorization': 'LOW '+IA_ACCESS_KEY+':'+IA_SECRET_KEY
}

