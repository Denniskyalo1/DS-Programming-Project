import threading
import requests
from flask import Flask, jsonify, request

from hash_ring import ConsistentHashRing, random_request_id

app = Flask(__name__)

ring = ConsistentHashRing()
lock = threading.RLock()


def bootstrap_manual_servers():
    with lock:
        ring.add_server("manual_s1")
        ring.add_server("manual_s2")


@app.route("/rep", methods=["GET"])
def rep():
    with lock:
        hosts = ring.hostnames()
    return jsonify({
        "message": {"N": len(hosts), "replicas": hosts},
        "status": "successful"
    }), 200


@app.route("/<path:path>", methods=["GET"])
def route_request(path):
    with lock:
        if ring.count() == 0:
            return jsonify({
                "message": "<Error> No servers available",
                "status": "failure"
            }), 400
        hostname = ring.get_server_for_request(random_request_id())

    try:
        resp = requests.get(f"http://{hostname}:5000/{path}", timeout=3)
        if resp.status_code == 404:
            return jsonify({
                "message": f"<Error> '/{path}' endpoint does not exist in server replicas",
                "status": "failure"
            }), 400
        return (resp.content, resp.status_code, resp.headers.items())
    except requests.exceptions.RequestException:
        return jsonify({
            "message": f"<Error> Server '{hostname}' unreachable",
            "status": "failure"
        }), 502


if __name__ == "__main__":
    bootstrap_manual_servers()
    app.run(host="0.0.0.0", port=5000)