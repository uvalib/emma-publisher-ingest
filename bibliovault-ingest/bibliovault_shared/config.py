# import logging
import os

BV_REPOSITORY_NAME = os.environ.get('BV_REPOSITORY_NAME','biblioVault')
EMMA_INGESTION_LIMIT = int(os.environ.get('EMMA_INGESTION_LIMIT', 100))

