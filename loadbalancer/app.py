import os
import random
import string
import threading
import time
import requests
from flask import Flask, jsonify, request

# Import the consistent hashing implementation
from hash_ring import ConsistentHashRing, random_request_id

# Flask application
app = Flask(__name__)

# Global hash ring and thread lock for synchronization
ring = ConsistentHashRing()
lock = threading.RLock()


# Helper Functions
def generate_random_hostname():
    return "server_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=6))


def deploy_docker_container(hostname):
    command = (
        f"docker run --name {hostname} "
        f"--network net1 "
        f"--network-alias {hostname} "
        f"-e SERVER_ID={hostname} "
        f"-d server_image:latest"
    )

    res = os.popen(command).read().strip()

    if len(res) == 0:
        print(f"[Error] Unable to start container: {hostname}")
        return False

    print(f"[Success] Started container: {hostname}")
    return True


def destroy_docker_container(hostname):
    command = f"docker stop {hostname} && sudo docker rm {hostname}"
    os.system(command)
    print(f"[Cleanup] Destroyed container: {hostname}")


def bootstrap_initial_servers():
    initial_hosts = ["server_1", "server_2", "server_3"]

    with lock:
        for host in initial_hosts:
            if deploy_docker_container(host):
                ring.add_server(host)


# REST API Endpoints
@app.route("/rep", methods=["GET"])
def rep():
    with lock:
        hosts = ring.hostnames()

    return jsonify({
        "message": {
            "N": ring.count(),
            "replicas": hosts
        },
        "status": "successful"
    }), 200


@app.route("/add", methods=["POST"])
def add_servers():
    data = request.get_json() or {}
    n = data.get("n", 0)
    hostnames = data.get("hostnames", [])

    # Reject invalid requests
    if len(hostnames) > n:
        return jsonify({
            "message": "<Error> Length of hostname list is more than newly added instances",
            "status": "failure"
        }), 400

    with lock:
        current_hosts = ring.hostnames()

        final_hostnames = list(hostnames)

        # Generate missing hostnames automatically
        while len(final_hostnames) < n:
            new_name = generate_random_hostname()

            if new_name not in current_hosts:
                final_hostnames.append(new_name)

        seen_hosts = set(current_hosts)

        # Deploy each new server
        for host in final_hostnames:

            if host in seen_hosts:
                print(f"[Skip] '{host}' already exists in the ring")
                continue

            if deploy_docker_container(host):
                ring.add_server(host)
                seen_hosts.add(host)

        current_hosts = ring.hostnames()

    return jsonify({
        "message": {
            "N": ring.count(),
            "replicas": current_hosts
        },
        "status": "successful"
    }), 200


@app.route("/rm", methods=["DELETE"])
def remove_servers():
    data = request.get_json() or {}

    n = data.get("n", 0)
    hostnames = data.get("hostnames", [])

    if len(hostnames) > n:
        return jsonify({
            "message": "<Error> Length of hostname list is more than removable instances",
            "status": "failure"
        }), 400

    with lock:

        current_hosts = ring.hostnames()

        targets_to_remove = []

        # Remove explicitly requested servers first
        for host in hostnames:
            if host in current_hosts:
                targets_to_remove.append(host)

        remaining_count = n - len(targets_to_remove)

        available_randoms = [
            h for h in current_hosts
            if h not in targets_to_remove
        ]

        if remaining_count > len(available_randoms):
            remaining_count = len(available_randoms)

        # Randomly choose remaining replicas
        targets_to_remove.extend(
            random.sample(available_randoms, remaining_count)
        )

        # Remove from hash ring and destroy containers
        for host in targets_to_remove:
            ring.remove_server(host)
            threading.Thread(
                target=destroy_docker_container,
                args=(host,)
            ).start()

        updated_hosts = ring.hostnames()

    return jsonify({
        "message": {
            "N": ring.count(),
            "replicas": updated_hosts
        },
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

        # Generate a request ID and locate the target server
        req_id = random_request_id()
        hostname = ring.get_server_for_request(req_id)

    if not hostname:
        return jsonify({
            "message": "<Error> Server lookup failed",
            "status": "failure"
        }), 500

    try:
        # Forward request to selected replica
        resp = requests.get(
            f"http://{hostname}:5000/{path}",
            timeout=2
        )

        if resp.status_code == 404:
            return jsonify({
                "message": f"<Error> '/{path}' endpoint does not exist in server replicas",
                "status": "failure"
            }), 400

        return (
            resp.content,
            resp.status_code,
            resp.headers.items()
        )

    except requests.exceptions.RequestException:

        return jsonify({
            "message": f"<Error> Server '{hostname}' unreachable",
            "status": "failure"
        }), 502


# Heartbeat Monitoring
def heartbeat_monitor():
    print("[Background Thread] Heartbeat checker monitoring activated.")

    while True:

        time.sleep(4)

        with lock:
            active_servers = ring.hostnames()

        for server in active_servers:

            try:
                resp = requests.get(
                    f"http://{server}:5000/heartbeat",
                    timeout=2
                )

                if resp.status_code != 200:
                    raise requests.exceptions.RequestException()

            except (requests.exceptions.RequestException, Exception):

                print(f"[Alert] Heartbeat failed for {server}")

                with lock:

                    active_servers = ring.hostnames()

                    if server in active_servers:
                        ring.remove_server(server)

                        threading.Thread(
                            target=destroy_docker_container,
                            args=(server,)
                        ).start()

                    # Launch replacement replica
                    new_host = generate_random_hostname()

                    if deploy_docker_container(new_host):
                        ring.add_server(new_host)


# Program Entry Point
if __name__ == "__main__":

    # Start the initial replicas
    bootstrap_initial_servers()

    # Start heartbeat monitoring in the background
    bg_heartbeat = threading.Thread(
        target=heartbeat_monitor,
        daemon=True
    )
    bg_heartbeat.start()

    # Launch the Flask load balancer
    app.run(host="0.0.0.0", port=5000)