#!/bin/bash
cd root

if [ ! -f "pubsub/pubsub-app.py" ];
then
# Files do not exist in the VM yet
echo "Installing required files..."

gcloud storage cp -r gs://bu-ds561-eawang-hw10-code-storage/pubsub/ /root/

sudo apt-get install python3-pip --no-install-recommends -y
pip install -r pubsub/requirements.txt

# Start pubsub app
python3 pubsub/pubsub-app.py

else
# Files already imported, just restart the app
python3 pubsub/pubsub-app.py
fi
