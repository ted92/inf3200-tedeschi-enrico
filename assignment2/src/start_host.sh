#!/bin/sh

# Start a number of nodes on a host

HOST="$1"
START_PORT="$2"
JOIN_HOST_PORT="$3"
COUNT="$4"

NODE_SCRIPT="$(pwd)/node2_http.py"
LOG_FILE="$(pwd)/tmp_shared_log.txt"
HOSTS_FILE="$(pwd)/tmp_running_hosts.txt"

if [ -z "$HOST" ]
then
    HOST=localhost
fi

if [ -z "$START_PORT" ]
then
    START_PORT=8080
fi

if [ -n "$JOIN_HOST_PORT" ]
then
    JOIN_FLAGS="--join $JOIN_HOST_PORT"
    JOIN_TEXT="joining network at $JOIN_HOST_PORT"
else
    JOIN_FLAGS=""
    JOIN_TEXT="not joining any network"
fi

if [ -z "$COUNT" ]
then
    COUNT=1
fi

let END_PORT=$START_PORT+$COUNT-1
echo "Starting $COUNT nodes on $HOST:$START_PORT-$END_PORT $JOIN_TEXT"

echo "$HOST" >> "$HOSTS_FILE"

for p in `seq $START_PORT $END_PORT`
do
    echo "Starting $HOST:$p"
    (
        set -x
        ssh "$HOST" \
            python "$NODE_SCRIPT" -v $HOST:$p $JOIN_FLAGS \
            2>&1 >> "$LOG_FILE" &
        sleep 1
    )
done
