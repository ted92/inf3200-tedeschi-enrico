#!/bin/sh

USER="$(whoami)"
HOSTS_FILE="$(pwd)/tmp_running_hosts.txt"

for HOST in $(sort "$HOSTS_FILE" | uniq)
do
    echo -n "$HOST "
    ssh $HOST \
        killall -u "$USER" python
done
