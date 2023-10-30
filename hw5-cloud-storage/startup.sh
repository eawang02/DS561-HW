#!/bin/bash

cd /home/eawang

if [ ! -f "bu-ds561-eawang-hw5-server/http-server.py" ];
then
# Files do not exist in the VM yet
echo "Installing required files..."

gcloud storage cp -r gs://bu-ds561-eawang-hw5-server/ /home/eawang

sudo apt-get install python3-pip --no-install-recommends -y
pip install -r bu-ds561-eawang-hw5-server/requirements.txt
gcloud compute firewall-rules create hw5-sql-server --allow tcp:5000 --source-tags=hw5-sql-server --source-ranges=0.0.0.0/0

python3 bu-ds561-eawang-hw5-server/http-server.py

else
# Files already imported, just restart the server
python3 bu-ds561-eawang-hw5-server/http-server.py
fi

