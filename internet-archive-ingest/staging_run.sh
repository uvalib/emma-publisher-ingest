if [[ -f secret_keys.sh ]] ; then
    . secret_keys.sh
fi
export EMMA_INGESTION_LIMIT=200
export OPENSEARCH_URL=localhost:9200
export OPENSEARCH_INDEX=emma-federated-index-staging-1.0.1
export BASTION_HOST=54.236.31.64
export BASTION_USERNAME=ec2-user
export BASTION_REMOTE_HOST=vpc-emma-nonlive-ip5v3sq3r2im6pvyvjcadlgzvm.us-east-1.es.amazonaws.com
export BASTION_SSHKEY=bastion_staging.pem
export EMMA_STATUS_TABLE_NAME=emma_bookshare_loader_staging


