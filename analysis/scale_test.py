import requests
from collections import Counter
import csv
import time

BASE_URL = "http://localhost:5000"

results = []

for N in range(2, 7):
    print(f"\n===== Testing N = {N} =====")

    # Get current replicas
    rep = requests.get(f"{BASE_URL}/rep").json()
    current = rep["message"]["N"]

    # Adjust the number of replicas
    if current < N:
        requests.post(
            f"{BASE_URL}/add",
            json={"n": N - current, "hostnames": []}
        )
    elif current > N:
        requests.delete(
            f"{BASE_URL}/rm",
            json={"n": current - N, "hostnames": []}
        )

    # Give Docker a few seconds to finish
    time.sleep(5)

    counts = Counter()

    for _ in range(10000):
        r = requests.get(f"{BASE_URL}/home")
        if r.status_code == 200:
            server = r.json()["message"].split(": ")[1]
            counts[server] += 1

    average = sum(counts.values()) / len(counts)

    print("Distribution:")
    for server, count in sorted(counts.items()):
        print(f"  {server}: {count}")

    results.append([N, average])

with open("scaling_results.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Replicas", "Average Requests Per Server"])
    writer.writerows(results)

print("\nResults saved to scaling_results.csv")