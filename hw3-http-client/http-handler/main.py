import functions_framework
from flask import Flask
from google.cloud import storage
from google.cloud import pubsub_v1
from concurrent import futures
from typing import Callable

# For local testing:
# functions-framework --target receive_http_request --debug

ForbiddenCountries = ["North Korea", "Iran", "Cuba", "Myanmar", "Iraq",
                      "Libya", "Sudan", "Zimbabwe", "Syria"]


@functions_framework.http
def receive_http_request(request):
    origin_country, request_method, file = parse_request(request)
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
        print("Request received from forbidden origin country: ", origin_country)

        return response

    # Check request type (only accept GET, reject others with 501 error)
    if (request_method != "GET"):
        response.response = "Invalid request method, access denied."
        response.status = 501

        # Send to Cloud Logging
        print("Request received with invalid request method: ", request_method)

        return response

    # Check for file name in bucket, if not found, give 404 error
    storage_client = storage.Client()
    bucket_name = "bu-ds561-eawang-hw2-pagerank"
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.get_blob(file)
    if not blob:
        response.response = "File not found."
        response.status = 404

        # Send to Cloud Logging
        print("Request received for non-existing file: ", file)

        return response

    # Return file to requesting client
    with blob.open('r') as f:
        contents = f.read()
        response.response = contents

    return response

def parse_request(request):
    method = request.method
    country = request.headers.get("X-country")
    file = request.url.split('/')[-1]

    return country, method, file