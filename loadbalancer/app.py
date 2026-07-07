import os
import random
import string
import threading
import time
import requests
from flask import Flask, jsonify, request

from hash_ring import ConsistentHashRing

app = Flask(__name__)

ring = ConsistentHashRing()
lock = threading.RLock()

# Helper to generate random hostnames when needed
def generate_random_hostname():
    return "server_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=6))

# Helper to deploy an actual Docker container instance on the shared network
def deploy_docker_container(hostname):
    # Using the exact pattern recommended in Appendix C of your lab handout
    command = f"sudo docker run --name {hostname} --network net1 --network-alias {hostname} -e SERVER_ID={hostname} -d my-server-image:latest"
    res = os.popen(command).read().strip()
    if len(res) == 0:
        print(f"[Error] Unable to start container: {hostname}")
        return False
    print(f"[Success] Started container: {hostname}")
    return True

# Helper to clean up and destroy a Docker container instance
def destroy_docker_container(hostname):
    command = f"sudo docker stop {hostname} && sudo docker rm {hostname}"
    os.system(command)
    print(f"[Cleanup] Destroyed container: {hostname}")

def bootstrap_initial_servers():
    """Initializes the environment with the default N=3 replicas"""
    initial_hosts = ["server_1", "server_2", "server_3"]
    with lock:
        for host in initial_hosts:
            if deploy_docker_container(host):
                ring.add_server(host)

@app.route("/rep", methods=["GET"])
def rep():
    with lock:
        hosts = list(ring.server_vnodes.keys())
    return jsonify({
        "message": {
            "N": len(hosts),
            "replicas": hosts
        },
        "status": "successful"
    }), 200

@app.route("/add", methods=["POST"])
def add_servers():
    data = request.get_json() or {}
    n = data.get("n", 0)
    hostnames = data.get("hostnames", [])

    # Sanity Check 1: Hostnames array must not exceed 'n' instances
    if len(hostnames) > n:
        return jsonify({
            "message": "<Error> Length of hostname list is more than newly added instances",
            "status": "failure"
        }), 400

    with lock:
        # Fill remaining hostnames with random labels if short
        final_hostnames = list(hostnames)
        while len(final_hostnames) < n:
            new_name = generate_random_hostname()
            if new_name not in ring.server_vnodes:
                final_hostnames.append(new_name)

        # Deploy each new server container instance
        for host in final_hostnames:
            if deploy_docker_container(host):
                ring.add_server(host)

        current_hosts = list(ring.server_vnodes.keys())

    return jsonify({
        "message": {
            "N": len(current_hosts),
            "replicas": current_hosts
        },
        "status": "successful"
    }), 200

@app.route("/rm", methods=["DELETE"])
def remove_servers():
    data = request.get_json() or {}
    n = data.get("n", 0)
    hostnames = data.get("hostnames", [])

    # Sanity Check 1: Hostnames specified must not exceed 'n' instances
    if len(hostnames) > n:
        return jsonify({
            "message": "<Error> Length of hostname list is more than removable instances",
            "status": "failure"
        }), 400

    with lock:
        current_hosts = list(ring.server_vnodes.keys())
        
        # Build the exact set of containers to tear down
        targets_to_remove = []
        for host in hostnames:
            if host in current_hosts:
                targets_to_remove.append(host)

        # Pick random active servers if fewer specific names were supplied
        remaining_count = n - len(targets_to_remove)
        available_randoms = [h for h in current_hosts if h not in targets_to_remove]
        
        if remaining_count > len(available_randoms):
            remaining_count = len(available_randoms)

        targets_to_remove.extend(random.sample(available_randoms, remaining_count))

        # Teardown containers and remove them from the mapping engine
        for host in targets_to_remove:
            ring.remove_server(host)
            # Run in separate thread to prevent blocking client response
            threading.Thread(target=destroy_docker_container, args=(host,)).start()

        updated_hosts = list(ring.server_vnodes.keys())

    return jsonify({
        "message": {
            "N": len(updated_hosts),
            "replicas": updated_hosts
        },
        "status": "successful"
    }), 200

@app.route("/<path:path>", methods=["GET"])
def route_request(path):
    # Standardize path routing checking
    with lock:
        if not ring.server_vnodes:
            return jsonify({
                "message": "<Error> No servers available",
                "status": "failure"
            }), 400
        
        # Generate a random 6-digit number as specified by the assignment sheet
        req_id = random.randint(100000, 999999)
        hostname = ring.get_server(req_id)

    if not hostname:
        return jsonify({"message": "<Error> Server lookup failed", "status": "failure"}), 500

    try:
        resp = requests.get(f"http://{hostname}:5000/{path}", timeout=2)
        return (resp.content, resp.status_code, resp.headers.items())
    except requests.exceptions.HTTPError:
        return jsonify({
            "message": f"<Error> '/{path}' endpoint does not exist in server replicas",
            "status": "failure"
        }), 400
    except requests.exceptions.RequestException:
        return jsonify({
            "message": f"<Error> Server '{hostname}' unreachable",
            "status": "failure"
        }), 502

def heartbeat_monitor():
    """Background loop checking server health status to ensure auto-healing functionality"""
    print("[Background Thread] Heartbeat checker monitoring activated.")
    while True:
        time.sleep(4)  # Poll cluster every 4 seconds
        with lock:
            active_servers = list(ring.server_vnodes.keys())

        for server in active_servers:
            try:
                # Attempt an internal health ping to the server
                resp = requests.get(f"http://{server}:5000/heartbeat", timeout=2)
                if resp.status_code != 200:
                    raise requests.exceptions.RequestException()
            except (requests.exceptions.RequestException, Exception):
                print(f"[Alert] Heartbeat failed for container: {server}. Spawning recovery node...")
                with lock:
                    # Clean out the dead node from our hash ring mapping structure
                    if server in ring.server_vnodes:
                        ring.remove_server(server)
                        threading.Thread(target=destroy_docker_container, args=(server,)).start()
                    
                    # Spawn a completely fresh replacement instance with a random hostname
                    new_host = generate_random_hostname()
                    if deploy_docker_container(new_host):
                        ring.add_server(new_host)

if __name__ == "__main__":
    # Launch initial N=3 system containers
    bootstrap_initial_servers()
    
    # Run the continuous health checking auto-healing background thread
    bg_heartbeat = threading.Thread(target=heartbeat_monitor, daemon=True)
    bg_heartbeat.start()
    
    app.run(host="0.0.0.0", port=5000)
