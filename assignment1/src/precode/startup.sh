#!/bin/bash          

# Executable
directory="/home/mst056/processes/";
executable="node.py";

# Lists of nodes
nodes=( "compute-1-1" "compute-1-2" "compute-1-3")

# Stop any running processes
for node in "${nodes[@]}"
do
  ssh $node bash -c "'pkill -f $executable'"
done

# Boot all processes
for node in "${nodes[@]}"
do
  echo "Booting node" $node
  nohup ssh $node bash -c "'python $directory$executable'"  > /dev/null 2>&1 &
done

# Wait/Run benchmarks
HEALTY=1
while [ $HEALTY -eq 1  ]; do 
  sleep 1
  echo "Checking if each node is alive and well..."
  for node in "${nodes[@]}"
  do
    if ssh -q $node ps aux | grep $executable > /dev/null 2>&1 ;
    then
      echo "$node is alive"
    else
      echo "$node is dead"
      let HEALTY=0
    fi
  done
done

# Stop 
for node in "${nodes[@]}"
do
  echo "Stopping node" $node
  ssh $node bash -c "'pkill -f $executable'"
done
