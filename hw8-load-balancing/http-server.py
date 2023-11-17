
from flask import Flask, request
from google.cloud import storage
from google.cloud import pubsub_v1
import google.cloud.logging
from concurrent import futures
from typing import Callable
import logging
import waitress

import os
from dotenv import load_dotenv

app = Flask(__name__)
req_methods = ['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH']
ForbiddenCountries = ["North Korea", "Iran", "Cuba", "Myanmar", "Iraq",
                      "Libya", "Sudan", "Zimbabwe", "Syria"]

logging_client = google.cloud.logging.Client()
logging_client.setup_logging()

load_dotenv()
config = os.environ

@app.route('/<bucket_name>/<file>', defaults={'dir': ''}, methods=req_methods)
@app.route('/<bucket_name>/<dir>/<file>', methods=req_methods)
def main(bucket_name, dir, file):
    req_headers = parse_request(request, file)
    response = Flask.response_class(response="Response")
    response.status = 200
    response.headers = {}
    response.headers.update({'X-server-zone': config['ZONE']})


    # Check request's origin country, if forbidden, send to app #2 through pub/sub w/ 400 error
    if (req_headers['is_banned']):
        response.response = "Forbidden origin country, access denied."
        response.status = 400

        # Send to Cloud Logging
        message = "Request received from forbidden origin country: " + req_headers['country']
        logging.error(message)
        # print(message)

        return response

    # Check request type (only accept GET, reject others with 501 error)
    if (req_headers['method'] != "GET"):
        response.response = "Invalid request method, access denied."
        response.status = 501

        # Send to Cloud Logging
        message = "Request received with invalid request method: " + req_headers['method']
        logging.error(message)
        # print(message)

        return response

    # Check for file name in bucket, if not found, give 404 error
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.get_blob(req_headers['requested_file'])
    if not blob:
        response.response = "File not found."
        response.status = 404

        # Send to Cloud Logging
        message = "Request received for non-existing file: " + req_headers['requested_file']
        logging.error(message)
        # print(message)

        return response

    # Return file to requesting client
    with blob.open('r') as f:
        contents = f.read()
        response.response = contents

    return response

def parse_request(request, file):
    return {
        "method": request.method,
        "country": request.headers.get("X-country"),
        "client_ip": request.headers.get("X-client-IP"),
        "gender": request.headers.get("X-gender"),
        "age": request.headers.get("X-age"),
        "income": request.headers.get("X-income"),
        "time_of_day": request.headers.get("X-time"),
        "is_banned": request.headers.get("X-country") in ForbiddenCountries,
        "requested_file": file,
    }


print("Server starting...")
waitress.serve(app, host='0.0.0.0', port="5000")


