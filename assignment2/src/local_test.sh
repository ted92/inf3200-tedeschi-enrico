#!/bin/bash

test_join() {
    echo
    echo "---------------------------------------------------------------------"
    echo "Join up some nodes with verbose output to watch what happens."
    echo

    (
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
        sleep 1
        kill $(jobs -p)
    )
}

test_benchmark_tool() {
    echo
    echo "---------------------------------------------------------------------"
    echo "Join up nodes with quiet output and use tool to examine network."
    echo

    (
        set -x
        python -u ./node2_http.py localhost:8000 2>/dev/null &
        sleep 1
        python -u ./node2_http.py localhost:8001 --join localhost:8000 &
        sleep 1
        python -u ./node2_http.py localhost:8002 --join localhost:8000 &
        sleep 1
        python -u ./node2_http.py localhost:8003 --join localhost:8000 &
        sleep 1
        python -u ./node2_http.py localhost:8004 --join localhost:8000 &
        sleep 1
        python -u leader_benchmark.py --ip localhost --port 8000
        sleep 1
        kill $(jobs -p)
    )
}

test_election() {
    echo
    echo "---------------------------------------------------------------------"
    echo "Test elections"
    echo

    (
        # set -x
        MAX=10

        python -u ./node2_http.py localhost:8000 &
        sleep 1

        for i in $(seq 1 $MAX)
        do
            let n=$i+1
            echo "Starting another node. Total: $n"
            let PORT=8000+$i
            python -u ./node2_http.py localhost:$PORT --join localhost:8000 &
            sleep 1
            echo "Kicking off election with $n nodes"
            curl -X POST http://localhost:$PORT/election
            sleep 1
        done

        kill $(jobs -p)
    )
}

test_join
sleep 2
test_benchmark_tool
sleep 2
test_election
