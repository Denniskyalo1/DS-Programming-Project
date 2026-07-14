import requests
from collections import Counter
import csv

# Endpoint exposed by the load balancer
URL = "http://localhost:5000/home"

# Total number of requests to send during the benchmark
TOTAL_REQUESTS = 10000

# Stores the number of requests handled by each server
counts = Counter()

print(f"Sending {TOTAL_REQUESTS} requests...")

# Send requests to the load balancer
for i in range(TOTAL_REQUESTS):
    r = requests.get(URL)

    # Ignore failed requests
    if r.status_code != 200:
        continue

    # Extract the responding server name from the JSON response
    server = r.json()["message"].split(": ")[1]
    counts[server] += 1

print("\nResults:\n")

# Display the request distribution
for server, count in sorted(counts.items()):
    print(f"{server}: {count}")

# Save the benchmark results to a CSV file for plotting
with open("distribution.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Server", "Requests"])

    for server, count in sorted(counts.items()):
        writer.writerow([server, count])

print("\nSaved results to distribution.csv")