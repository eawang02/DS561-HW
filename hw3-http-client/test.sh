#!/bin/bash

url="https://http-handler-caskf24nqa-uc.a.run.app/bu-ds561-eawang-hw2-pagerank/1.html"

echo "Testing PUT, POST, DELETE, HEAD, OPTIONS, TRACE, CONNECT PATCH commands"
curl -X PUT $url -I
curl -X POST $url -I
curl -X DELETE $url -I
curl -X HEAD $url -I
curl -X OPTIONS $url -I
curl -X TRACE $url -I
curl -X CONNECT $url -I
curl -X PATCH $url -I
