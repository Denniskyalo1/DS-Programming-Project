import requests
from collections import Counter
import csv
import time

# Base URL of the load balancer
BASE_URL = "http://localhost:5000"

# Stores the average requests per server for each experiment
results = []

# Test the system with different numbers of replicas
for N in range(2, 7):
    print(f"\n===== Testing N = {N} =====")

    # Retrieve the current number of active replicas
    rep = requests.get(f"{BASE_URL}/rep").json()
    current = rep["message"]["N"]

    # Scale up by adding replicas if required
    if current < N:
        requests.post(
            f"{BASE_URL}/add",
            json={"n": N - current, "hostnames": []}
        )

    # Scale down by removing replicas if required
    elif current > N:
        requests.delete(
            f"{BASE_URL}/rm",
            json={"n": current - N, "hostnames": []}
        )

    # Allow Docker enough time to create or remove containers
    time.sleep(5)

    # Count the number of requests handled by each server
    counts = Counter()

    # Send 10,000 requests through the load balancer
    for _ in range(10000):
        r = requests.get(f"{BASE_URL}/home")

        if r.status_code == 200:
            server = r.json()["message"].split(": ")[1]
            counts[server] += 1

    # Calculate the average requests handled per server
    average = sum(counts.values()) / len(counts)

    print("Distribution:")

    # Display the request distribution for the current experiment
    for server, count in sorted(counts.items()):
        print(f"  {server}: {count}")

    # Store the results for later analysis
    results.append([N, average])

# Save the scaling experiment results to a CSV file
with open("scaling_results.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Replicas", "Average Requests Per Server"])
    writer.writerows(results)

print("\nResults saved to scaling_results.csv")