#!/bin/bash
cd root

if [ ! -f "server/http-server.py" ];
then
# Files do not exist in the VM yet
echo "Installing required files..."

gcloud storage cp -r gs://bu-ds561-eawang-hw10-code-storage/server/ /root/

sudo apt-get install python3-pip --no-install-recommends -y
pip install -r server/requirements.txt

# Create mini-internet files
python3 server/generate-content.py -n 1000
gsutil -m cp -r *.html gs://bu-ds561-eawang-hw10-pagerank/

# Start server
python3 server/http-server.py

else
# Files already imported, just restart the server
python3 server/http-server.py
fi

