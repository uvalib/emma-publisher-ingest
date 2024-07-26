# import logging
import os

OA_REPOSITORY_NAME = os.environ.get('BV_REPOSITORY_NAME','biblioVault')
OA_SCRAPE_URL = 'https://api.openalex.org/works'
EMMA_INGESTION_LIMIT = int(os.environ.get('EMMA_INGESTION_LIMIT', 200))
OA_RETRY = int(os.environ.get('OA_RETRY', 2))
OA_RETRIEVALS = int(os.environ.get('OA_RETRIEVALS', 500))
OA_TIMEOUT = int(os.environ.get('OA_TIMEOUT', 120))
OA_PAGE_SIZE = int(os.environ.get('OA_PAGE_SIZE', 200))

STATUS_TABLE_PREFIX = os.environ.get('EMMA_STATUS_TABLE_PREFIX', 'OA_')
DYNAMODB_LOADER_TABLE = os.environ.get('EMMA_STATUS_TABLE_NAME', 'emma_bookshare_loader')        

DATE_UPDATED_FIELD = 'updated_date'
DATE_LOWER_BOUNDARY_FIELD = 'from_created_date'
DATE_UPPER_BOUNDARY_FIELD = 'NULL'
SEARCH_PARAMS = {'per_page': OA_PAGE_SIZE,
                 'filter': 'is_oa:true,type:article',
                 }
