#!/bin/bash

sudo apt-get update
sudo apt-get install apache2 -y
sudo service apache2 restart
echo '<!doctype html><html><body><h1>www1</h1></body></html>' | tee /var/www/html/index.html

cd /home/eawang

if [ ! -f "bu-ds561-eawang-hw8-server/http-server.py" ];
then
# Files do not exist in the VM yet
echo "Installing required files..."

gcloud storage cp -r gs://bu-ds561-eawang-hw8-server/ /home/eawang

sudo apt-get install python3-pip --no-install-recommends -y
sudo pip install -r bu-ds561-eawang-hw8-server/requirements.txt

sudo python3 bu-ds561-eawang-hw8-server/http-server.py

else
# Files already imported, just restart the server
sudo python3 bu-ds561-eawang-hw8-server/http-server.py
fi

