if [[ -f secret_keys.sh ]] ; then
    . secret_keys.sh
fi
export EMMA_INGESTION_LIMIT=500
export OPENSEARCH_URL=vpc-emma-nonlive-ip5v3sq3r2im6pvyvjcadlgzvm.us-east-1.es.amazonaws.com
export OPENSEARCH_INDEX=emma-federated-index-staging-1.0.1
export EMMA_STATUS_TABLE_NAME=emma_bookshare_loader_staging


