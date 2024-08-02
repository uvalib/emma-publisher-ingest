#!/bin/bash

if [[ "$1" != "staging" && "$1" != "production" ]] ; then
    echo "Usage $0 staging|production "'[{date}|"all"|"newest"]'
else
    index=$1
    shift
fi

datefile=./index_date_${index}.txt

if [[ "$1" != "" ]] ; then
    date=$1
elif [[ -f ${datefile} ]] ;  then
    date=`cat ${datefile}`
else
    date="all"
fi

is_local=false

scriptname="${index}_run_local.sh"

. ${scriptname}

# check for local access to opensearch
echo "Trying to reach https://$OPENSEARCH_URL"
curl -s -m 2 -X GET "https://$OPENSEARCH_URL/_search"  -H 'Content-Type: application/json' -d '@emma_localhost_test_query2.json' > /dev/null
if [[ $? == 0 ]]; then
    echo "Local to OpenSearch index"
    is_local=true
else
    echo "Not local to OpenSearch index, will use tunnel"
    scriptname="${index}_run_tunnel.sh"
    . ${scriptname}
fi

command="cat"
if [[ "$date" == "all" ]]; then
    my_date="2024-01-01"
elif [[ "$date" == "newest" ]]; then
    my_date="2024-01-01"
    command="tail -1"
else 
    my_date=$date
fi

BUCKET=bibliovault-transfer-${index}
echo "looking in bucket: ${BUCKET}"

for line in `aws s3 ls "s3://${BUCKET}/" | egrep "*.xml" | sed -s 's/  */#/g' | sort | $command`
do 
    datestr=`echo $line | cut -d '#' -f 1`
    epoch1=`date -d "$datestr" +%s`
    epoch2=`date -d "$my_date" +%s`
    file=`echo $line | cut -d '#' -f 4`
    if [[ $epoch1 -ge $epoch2 ]]; then
        echo "process $datestr : $file"
        echo "------------------------------------------------------------------"
        pipenv run python -u main-cmdline.py  --bucket bibliovault-transfer-staging  --key ${file}
        echo "------------------------------------------------------------------"
        echo " "
    else
        echo "dont process $datestr : $file"
    fi
done

date "+%Y-%m-%d" > $datefile
