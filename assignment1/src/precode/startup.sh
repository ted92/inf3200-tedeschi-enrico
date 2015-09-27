#!/bin/bash          
# vim: set sts=2 sw=2 et:

num_hosts=$1

if [ -z "$num_hosts" ]
then
  let num_hosts=3
  cat <<-EOF

	Using default of $num_hosts random hosts.
	Use a numerical argument to change the number of hosts.

	For example:
	    $(basename $0) 6


	EOF
fi

# Executable
directory=`pwd` #current working directory
executable="node.py";

# Lists of nodes
nodes=$(rocks list host | grep compute | cut -d" " -f1 | sed 's/.$//' | shuf | head -n "$num_hosts")

echo "Nodes:"
echo $nodes


# Stop any running processes
for node in $nodes
do
  ssh $node bash -c "'pgrep -f '$directory/$executable' | xargs kill'"
done

# Boot all processes
for node in $nodes
do
  echo "Booting node" $node
  nohup ssh $node bash -c "'python $directory/$executable'"  > /dev/null 2>&1 &
done

# Wait/Run benchmarks
HEALTY=1
QUIT=0
SLEEP_SECONDS=2
while [ $HEALTY -eq 1 ] && [ $QUIT -eq 0 ]; do
  echo "Checking if each node is alive and well..."
  for node in $nodes
  do
    if ssh -q $node ps aux | grep $executable > /dev/null 2>&1 ;
    then
      echo "$node is alive"
    else
      echo "$node is dead"
      let HEALTY=0
    fi
  done

  if [ $HEALTY -eq 1 ]
  then
    read -t $SLEEP_SECONDS -p "Sleeping $SLEEP_SECONDS seconds. Press ENTER to shutdown." \
      && echo "Caught ENTER. Shutting down..." \
      && let QUIT=1
    echo
  else
    echo "Cluster is no longer healthy. Shutting down..."
  fi
done

# Stop 
for node in $nodes
do
  ssh $node bash -c "'pgrep -f '$directory/$executable' | xargs kill'"
  if ssh -q $node ps aux | grep $executable > /dev/null 2>&1 ;
  then
    echo "Error: unable to stop $node"
  else
    echo "Shut down $node"
  fi
done
