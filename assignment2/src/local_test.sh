#!/bin/bash

set -x

python -u ./node2_http.py -v localhost:8000 &
sleep 1
python -u ./node2_http.py -v localhost:8001 --join localhost:8000 &
sleep 1
python -u ./node2_http.py -v localhost:8002 --join localhost:8001 &
sleep 1
curl -vX GET http://localhost:8000/getNodes
curl -vX GET http://localhost:8001/getNodes
curl -vX GET http://localhost:8002/getNodes

curl -vX GET http://localhost:8000/getCurrentLeader
curl -vX GET http://localhost:8001/getCurrentLeader
curl -vX GET http://localhost:8002/getCurrentLeader
sleep 5
kill $(jobs -p)
