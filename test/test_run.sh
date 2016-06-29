#!/usr/bin/env bash

set -x

REMOTE_HADOOP_WEBSERVICE_HOST="http://127.0.0.1:8000"
#REMOTE_HADOOP_WEBSERVICE_HOST="http://129.114.111.66:8000"
CALLBACK_URL="http://requestb.in/oxkgbuox"
USER="foo"
PASSWORD="bar"

function extract_id {

    RESULT=$(echo $1 | sed 's/.*"id"://g' | sed 's/,.*//g')

    echo "$RESULT"
}

function extract_token {

    RESULT=$(echo $1 | sed 's/.*"token"://g' | sed 's/,.*//g' | sed 's/"//g' | sed 's/}//g')

    echo "$RESULT"
}

curl --data "username=$USER&password=$PASSWORD" -X POST $REMOTE_HADOOP_WEBSERVICE_HOST/register_new_user/
TOKEN_CREATION_OUTPUT=$(curl --header "username: $USER" --header "password: $PASSWORD" -X GET $REMOTE_HADOOP_WEBSERVICE_HOST/generate_new_token/)
TOKEN=$(extract_token $TOKEN_CREATION_OUTPUT)

echo $TOKEN

# Clean output file in FS folder to prevent interference between tests
curl --header "token: $TOKEN" -X GET $REMOTE_HADOOP_WEBSERVICE_HOST/fs/rm/test.txt/

# Clean output file in FS folder to prevent interference between tests
curl --header "token: $TOKEN" -X GET $REMOTE_HADOOP_WEBSERVICE_HOST/fs/rm/output.txt/

# Upload local files to the application
curl --header "token: $TOKEN" -i -X POST -F 'data=@test.sh' $REMOTE_HADOOP_WEBSERVICE_HOST/fs/upload/test.sh/

# Run "test.sh" with bash
curl --header "token: $TOKEN" -i -X GET  $REMOTE_HADOOP_WEBSERVICE_HOST/fs/run/test.sh/

sleep 5

# Download the "output.txt" file
curl --header "token: $TOKEN" -X GET $REMOTE_HADOOP_WEBSERVICE_HOST/fs/download/out.txt/


exit 0
