#!/bin/bash

if [ ! -f "/home/eawang/bu-ds561-eawang-hw4-server/http-server.py" ];
then
# Files do not exist in the VM yet
echo "Installing required files..."

gcloud storage cp -r gs://bu-ds561-eawang-hw4-server/ /home/eawang/

sudo su <<EOF
apt-get install python3-pip --no-install-recommends -y
pip install -r /home/eawang/bu-ds561-eawang-hw4-server/requirements.txt
gcloud compute firewall-rules create hw4-server-instance --allow tcp:5000 --source-tags=hw4-server-instance --source-ranges=0.0.0.0/0
EOF
/usr/bin/python3 /home/eawang/bu-ds561-eawang-hw4-server/http-server.py

else
# Files already imported, just restart the server
/usr/bin/python3 /home/eawang/bu-ds561-eawang-hw4-server/http-server.py
fi

