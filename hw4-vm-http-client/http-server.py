
from flask import Flask, request
from google.cloud import storage
from google.cloud import pubsub_v1
import google.cloud.logging
from concurrent import futures
from typing import Callable
import logging
import waitress

# Local testing: flask --app http-server.py run --debug --port=5000

app = Flask(__name__)
req_methods = ['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH']
ForbiddenCountries = ["North Korea", "Iran", "Cuba", "Myanmar", "Iraq",
                      "Libya", "Sudan", "Zimbabwe", "Syria"]

logging_client = google.cloud.logging.Client()
logging_client.setup_logging()


@app.route('/<bucket_name>/<file>', defaults={'dir': ''}, methods=req_methods)
@app.route('/<bucket_name>/<dir>/<file>', methods=req_methods)
def main(bucket_name, dir, file):
    origin_country, request_method = parse_request(request)
    response = Flask.response_class(response="Response")
    response.status = 200
    response.headers = {}


    # Check request's origin country, if forbidden, send to app #2 through pub/sub w/ 400 error
    if (origin_country in ForbiddenCountries):
        response.response = "Forbidden origin country, access denied."
        response.status = 400
        
        # Create Pub/Sub event to app #2
        publish_client = pubsub_v1.PublisherClient()
        topic_path = publish_client.topic_path("ds561cloudcomputing", "hw3-forbidden-requests")

        def get_callback(
            publish_future: pubsub_v1.publisher.futures.Future, data: str
        ) -> Callable[[pubsub_v1.publisher.futures.Future], None]:
            def callback(publish_future: pubsub_v1.publisher.futures.Future) -> None:
                try:
                    # Wait 60 seconds for the publish call to succeed.
                    publish_future.result(timeout=60)
                except futures.TimeoutError:
                    print(f"Publishing {data} timed out.")

            return callback

        publish_future = publish_client.publish(topic_path, origin_country.encode("utf-8"))
        publish_future.add_done_callback(get_callback(publish_future, origin_country))
        futures.wait([publish_future])

        # Send to Cloud Logging
        message = "Request received from forbidden origin country: " + origin_country
        logging.error(message)
        print(message)

        return response

    # Check request type (only accept GET, reject others with 501 error)
    if (request_method != "GET"):
        response.response = "Invalid request method, access denied."
        response.status = 501

        # Send to Cloud Logging
        message = "Request received with invalid request method: " + request_method
        logging.error(message)
        print(message)

        return response

    # Check for file name in bucket, if not found, give 404 error
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.get_blob(file)
    if not blob:
        response.response = "File not found."
        response.status = 404

        # Send to Cloud Logging
        message = "Request received for non-existing file: " + file
        logging.error(message)
        print(message)

        return response

    # Return file to requesting client
    with blob.open('r') as f:
        contents = f.read()
        response.response = contents

    return response

def parse_request(request):
    method = request.method
    country = request.headers.get("X-country")

    return country, method

print("Server starting...")
waitress.serve(app, host='0.0.0.0', port="5000")

