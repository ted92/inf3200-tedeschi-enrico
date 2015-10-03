#!/bin/bash          
# vim: set sts=2 sw=2 et:

nodes=$*

if [ -z "$nodes" ]
then
  nodes='compute-14-1 compute-15-1 compute-19-1'
  cat <<-EOF

	Using default list of nodes. To use different nodes, specify them on the
	command line. The helper script "list_random_hosts.sh" can give you a
	list to use.

	For example:
	    $(basename $0) compute-1-4 compute-15-0 compute-3-2 compute-6-0
	    $(basename $0) \$(./list_random_hosts.sh 6)


	EOF
fi

# Executable
directory=`pwd` #current working directory
executable="node.py";

#put the output into an array
nodes_array=($nodes)

echo "Nodes:"
echo $nodes

node_count=${#nodes_array[@]}
echo "$node_count total"


# Stop any running processes
for node in $nodes
do
  ssh $node bash -c "'pgrep -f '$directory/$executable' | xargs kill'"
done

# Boot all processes
for ((rank = 0; rank < node_count; rank++))
do
  #echo "Booting node" ${nodes_array[$rank]}
  # set the current node and the next node
  current=${nodes_array[$rank]}
  if [ $rank -ne $((node_count-1)) ]
  then next_node=${nodes_array[rank+1]}
  else next_node=${nodes_array[0]}
  fi
  
  #give the parameter to node.py
  nohup ssh $current bash -c "'python -u $directory/$executable $node_count $rank $next_node'" 2>&1 | sed "s/^/$current: /" &
done

# Run tests
sleep 2
#python storage_frontend.py --runtests $nodes

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
