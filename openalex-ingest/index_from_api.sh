#!/bin/bash

if [[ "$1" == "--debug" ]] ; then
    debug=$1
    shift
else
    debug=
fi

if [[ "$1" != "staging" && "$1" != "production" ]] ; then
    echo "Usage $0 staging|production "'[{date}|"newest"]'
    exit
else
    index=$1
    shift
fi

if [[ "$1" != "" ]] ; then
    date=$1
else
    date=""
fi

is_local=false

scriptname="${index}_run_local.sh"

. ${scriptname}

# check for local access to opensearch
echo "Trying to reach https://$OPENSEARCH_URL"
curl -s -m 2 -X GET "https://$OPENSEARCH_URL/_search"  -H 'Content-Type: application/json' -d '@shared/emma_localhost_test_query2.json' > /dev/null
if [[ $? == 0 ]]; then
    echo "Local to OpenSearch index"
    is_local=true
else
    echo "Not local to OpenSearch index, will use tunnel"
    scriptname="${index}_run_tunnel.sh"
    . ${scriptname}
fi

if [[ $date == "" ]]; then
    pipenv run python -u main-cmdline.py $debug
else
    pipenv run python -u main-cmdline.py --debug --start $date
fi

