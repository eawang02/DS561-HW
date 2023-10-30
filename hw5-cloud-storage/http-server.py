
from flask import Flask, request
from google.cloud import storage
from google.cloud import pubsub_v1
import google.cloud.logging
from concurrent import futures
from typing import Callable
import logging
import waitress

from google.cloud.sql.connector import Connector, IPTypes
import pymysql
import sqlalchemy
import os
from dotenv import load_dotenv

# Local testing: flask --app http-server.py run --debug --port=5001

app = Flask(__name__)
req_methods = ['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH']
ForbiddenCountries = ["North Korea", "Iran", "Cuba", "Myanmar", "Iraq",
                      "Libya", "Sudan", "Zimbabwe", "Syria"]

logging_client = google.cloud.logging.Client()
logging_client.setup_logging()

load_dotenv()
config = os.environ

insert_req = sqlalchemy.text(
    "INSERT INTO all_requests (country, client_ip, gender, age, income, is_banned, time_of_day, requested_file) "
    "VALUES (:country, :client_ip, :gender, :age, :income, :is_banned, :time_of_day, :requested_file);",
)

insert_invalid = sqlalchemy.text(
    "INSERT INTO invalid_requests (id, time_of_day, requested_file, error_code) "
    "VALUES (:id, :time_of_day, :requested_file, :error_code);",
)

connector = Connector()

# function to return the database connection object
def getconn():
    conn = connector.connect(
        config['INSTANCE_CONNECTION_NAME'],
        "pymysql",
        user=config['DATABASE_USER'],
        password=config['DATABASE_PASSWORD'],
        db=config['DATABASE_NAME'],
    )
    return conn

# create connection pool with 'creator' argument to our connection object function
pool = sqlalchemy.create_engine(
    "mysql+pymysql://",
    creator=getconn,
)


@app.route('/<bucket_name>/<file>', defaults={'dir': ''}, methods=req_methods)
@app.route('/<bucket_name>/<dir>/<file>', methods=req_methods)
def main(bucket_name, dir, file):
    req_headers = parse_request(request, file)
    response = Flask.response_class(response="Response")
    response.status = 200
    response.headers = {}


    # Check request's origin country, if forbidden, send to app #2 through pub/sub w/ 400 error
    if (req_headers['is_banned']):
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

        publish_future = publish_client.publish(topic_path, req_headers['country'].encode("utf-8"))
        publish_future.add_done_callback(get_callback(publish_future, req_headers['country']))
        futures.wait([publish_future])

        # Send to Cloud Logging
        message = "Request received from forbidden origin country: " + req_headers['country']
        logging.error(message)
        # print(message)

        insert_invalid_request(req_headers, 400)

        return response

    # Check request type (only accept GET, reject others with 501 error)
    if (req_headers['method'] != "GET"):
        response.response = "Invalid request method, access denied."
        response.status = 501

        # Send to Cloud Logging
        message = "Request received with invalid request method: " + req_headers['method']
        logging.error(message)
        # print(message)

        insert_invalid_request(req_headers, 501)

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

        insert_invalid_request(req_headers, 404)

        return response

    # Return file to requesting client
    with blob.open('r') as f:
        contents = f.read()
        response.response = contents

    insert_valid_request(req_headers)

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

def insert_valid_request(headers):
    with pool.connect() as db_conn:
        db_conn.execute(insert_req,
                        parameters={"country": headers["country"], "client_ip": headers["client_ip"],
                                    "gender": headers["gender"], "age": headers["age"], "income": headers["income"],
                                    "is_banned": headers["is_banned"], "time_of_day": headers["time_of_day"],
                                    "requested_file": headers["requested_file"]})
        db_conn.commit()

def insert_invalid_request(headers, error_code):
    with pool.connect() as db_conn:
        db_conn.execute(insert_req,
                        parameters={"country": headers["country"], "client_ip": headers["client_ip"],
                                    "gender": headers["gender"], "age": headers["age"], "income": headers["income"],
                                    "is_banned": headers["is_banned"], "time_of_day": headers["time_of_day"],
                                    "requested_file": headers["requested_file"]})
        
        last_id = db_conn.execute(sqlalchemy.text("SELECT LAST_INSERT_ID()")).fetchone()[0]

        db_conn.execute(insert_invalid,
                        parameters={"id": last_id, "time_of_day": headers["time_of_day"],
                                    "requested_file": headers["requested_file"], "error_code": error_code})
        
        db_conn.commit()


print("Server starting...")
waitress.serve(app, host='0.0.0.0', port="5000")


