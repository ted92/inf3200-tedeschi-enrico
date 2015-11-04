#!/bin/bash

set -x

# New round. Join up some nodes with verbose output to watch what happens.
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
sleep 1
kill $(jobs -p)


# New round. Join up nodes with quiet output and use tool to examine network.
sleep 1
python -u ./node2_http.py localhost:8000 2>/dev/null &
sleep 1
python -u ./node2_http.py localhost:8001 --join localhost:8000 2>/dev/null &
sleep 1
python -u ./node2_http.py localhost:8002 --join localhost:8000 2>/dev/null &
sleep 1
python -u ./node2_http.py localhost:8003 --join localhost:8000 2>/dev/null &
sleep 1
python -u ./node2_http.py localhost:8004 --join localhost:8000 2>/dev/null &
sleep 1
python -u leader_benchmark.py --ip localhost --port 8000
sleep 1
kill $(jobs -p)


# New round. Time a few elections
python -u ./node2_http.py localhost:8000 &
sleep 1
python -u ./node2_http.py localhost:8001 --join localhost:8000 &
sleep 1
python -u ./node2_http.py localhost:8002 --join localhost:8001 &
sleep 1
curl -vX POST http://localhost:8000/election
sleep 3
kill $(jobs -p)
