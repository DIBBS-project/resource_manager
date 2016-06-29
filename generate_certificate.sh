#!/bin/bash

rm -rf cert
mkdir cert
pushd cert

export PASSWORD="stairs_sun_cherry_screen"

openssl genrsa -des3 -passout pass:$PASSWORD -out server.pass.key 2048
openssl rsa -passin pass:$PASSWORD -in server.pass.key -out server.key
rm server.pass.key

openssl req -new -key server.key -passin pass:$PASSWORD \
-passout pass:$PASSWORD -out server.csr -days 1095 \
-subj /C=US/ST=City/L=City/O=company/OU=SSLServers/CN=localhost/emailAddress=user@localhost

openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt

popd

echo "certificate generated: the certificate is in cert/server.crt and the key is in cert/server.key"