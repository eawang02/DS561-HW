#!/bin/bash

# Create two "parallel" clients
for x in {0..1}; 
do
    python3 http-client.py -d 35.212.16.4 -b /bu-ds561-eawang-hw2-pagerank -n 50000 -p 5000 -i 10000 -r 1337 &
done

wait 

echo "Done."