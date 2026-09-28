#!/bin/sh
set -eu

CERT=/etc/nginx/certs/fullchain.pem
KEY=/etc/nginx/certs/privkey.pem
CONF_DIR=/etc/nginx/conf.d
TPL=/etc/nginx/mgmt-templates

if [ -s "${CERT}" ] && [ -s "${KEY}" ]; then
    cp "${TPL}/http-redirect.conf" "${CONF_DIR}/default.conf"
    cp "${TPL}/https.conf" "${CONF_DIR}/ssl.conf"
else
    cp "${TPL}/http.conf" "${CONF_DIR}/default.conf"
    rm -f "${CONF_DIR}/ssl.conf"
fi
