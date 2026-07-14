import requests
from collections import Counter
import csv

URL = "http://localhost:5000/home"
TOTAL_REQUESTS = 10000

counts = Counter()

print(f"Sending {TOTAL_REQUESTS} requests...")

for i in range(TOTAL_REQUESTS):
    r = requests.get(URL)

    if r.status_code != 200:
        continue

    server = r.json()["message"].split(": ")[1]
    counts[server] += 1

print("\nResults:\n")

for server, count in sorted(counts.items()):
    print(f"{server}: {count}")

with open("distribution.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Server", "Requests"])
    for server, count in sorted(counts.items()):
        writer.writerow([server, count])

print("\nSaved results to distribution.csv")