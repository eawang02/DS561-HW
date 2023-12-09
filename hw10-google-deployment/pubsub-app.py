
## Subscription client code taken from Google Cloud Documentation
## https://cloud.google.com/pubsub/docs/samples/pubsub-quickstart-subscriber?hl=en

from concurrent.futures import TimeoutError
from google.cloud import pubsub_v1

subscribe_client = pubsub_v1.SubscriberClient()
subscription_path = subscribe_client.subscription_path("ds561cloudcomputing", "pub-sub-subscription")

def callback(message: pubsub_v1.subscriber.message.Message) -> None:
    #print(f"Received {message}.")
    print("Request from forbidden country: ", bytes.decode(message.data))
    message.ack()

streaming_pull_future = subscribe_client.subscribe(subscription_path, callback=callback)
print(f"Listening for messages on {subscription_path}..\n")

# Wrap subscriber in a 'with' block to automatically call close() when done.
with subscribe_client:
    try:
        # When `timeout` is not set, result() will block indefinitely,
        # unless an exception is encountered first.
        #streaming_pull_future.result(timeout=5.0)

        streaming_pull_future.result()
    except TimeoutError:
        streaming_pull_future.cancel()  # Trigger the shutdown.
        streaming_pull_future.result()  # Block until the shutdown is complete.