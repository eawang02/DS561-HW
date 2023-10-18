#!/bin/bash

for n in {1..100};
do
    python3 http-client.py -d 35.212.16.4 -b /bu-ds561-eawang-hw2-pagerank -n 1000 -p 5000 &
done

wait

echo "Done."