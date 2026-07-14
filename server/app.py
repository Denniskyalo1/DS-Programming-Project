import os
from flask import Flask, jsonify

# Create the Flask application
app = Flask(__name__)

# Read the unique server identifier from the Docker environment.
# If not provided, use "unknown" as the default value.
SERVER_ID = os.environ.get("SERVER_ID", "unknown")


@app.route("/home", methods=["GET"])
def home():
    #Main endpoint served by each replica.
    return jsonify({
        "message": f"Hello from Server: {SERVER_ID}",
        "status": "successful"
    }), 200


@app.route("/heartbeat", methods=["GET"])
def heartbeat():
    #Health-check endpoint.
   return "", 200


if __name__ == "__main__":
    # Start the Flask server and listen on all network interfaces
    app.run(host="0.0.0.0", port=5000)