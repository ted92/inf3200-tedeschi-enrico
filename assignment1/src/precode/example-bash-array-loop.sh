#!/bin/bash

# Example of iteration over an array in Bash, with peek at next value.

nodes=$(ls)
nodes_array=($nodes)
num_nodes=${#nodes_array[@]}

cat <<-END
	nodes:          $nodes

	num_nodes       $num_nodes
END

for (( rank=0 ; rank < num_nodes; rank++ ))
do
    current=${nodes_array[$rank]}
    if [ $rank -ne $num_nodes ]
    then next=${nodes_array[rank+1]}
    else next=${nodes_array[0]}
    fi

    echo "$rank	$current		$next"
done
