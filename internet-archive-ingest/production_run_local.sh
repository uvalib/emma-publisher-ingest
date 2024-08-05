if [[ -f secret_keys.sh ]] ; then
    . secret_keys.sh
fi
export EMMA_INGESTION_LIMIT=500
export OPENSEARCH_URL=vpc-emma-index-production-glc53yq4angokfgqxlmzalupqe.us-east-1.es.amazonaws.com
export OPENSEARCH_INDEX=emma-federated-index-production
export EMMA_STATUS_TABLE_NAME=emma_bookshare_loader_production
