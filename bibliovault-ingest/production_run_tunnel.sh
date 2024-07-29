if [[ -f secret_keys.sh ]] ; then
    . secret_keys.sh
fi
export EMMA_INGESTION_LIMIT=50
export OPENSEARCH_URL=localhost:9200
export OPENSEARCH_INDEX=emma-federated-index-production
export BASTION_HOST=3.237.97.223
export BASTION_USERNAME=ec2-user
export BASTION_REMOTE_HOST=vpc-emma-index-production-glc53yq4angokfgqxlmzalupqe.us-east-1.es.amazonaws.com
export BASTION_SSHKEY=bastion_production.pem
