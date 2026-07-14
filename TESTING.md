# Testing

This document describes the test cases used to verify the functionality of the distributed load balancer.

---

## Prerequisites

Build the Docker images:

```bash
make build
```

Start the application:

```bash
make run
```

Verify that the system has started successfully:

```bash
curl http://localhost:5000/rep
```

Expected output:

```json
{
  "message": {
    "N": 3,
    "replicas": [
      "server_1",
      "server_2",
      "server_3"
    ]
  },
  "status": "successful"
}
```

---

# Test Case 1: Verify Request Routing

### Objective

Ensure that client requests are correctly routed to one of the active server replicas.

### Command

```bash
curl http://localhost:5000/home
```

### Expected Result

- Status code: 200
- The response identifies the server that handled the request.

Example:

```json
{
    "message": "Hello from Server: server_2",
    "status": "successful"
}
```

---

# Test Case 2: Invalid Endpoint

### Objective

Verify that invalid endpoints return an appropriate error.

### Command

```bash
curl http://localhost:5000/abcdef
```

### Expected Result

- Status code: 400
- Error message indicating the endpoint does not exist.

---

# Test Case 3: Add Server Replica

### Objective

Verify that the load balancer can dynamically add replicas.

### Command

```bash
curl -X POST http://localhost:5000/add \
-H "Content-Type: application/json" \
-d '{"n":1,"hostnames":[]}'
```

Verify:

```bash
curl http://localhost:5000/rep
```

### Expected Result

- Replica count increases by one.
- A new server appears in the replica list.

---

# Test Case 4: Remove Server Replica

### Objective

Verify that replicas can be removed dynamically.

### Command

```bash
curl -X DELETE http://localhost:5000/rm \
-H "Content-Type: application/json" \
-d '{"n":1,"hostnames":[]}'
```

Verify:

```bash
curl http://localhost:5000/rep
```

### Expected Result

- Replica count decreases by one.

---

# Test Case 5: Automatic Failure Recovery

### Objective

Verify that the heartbeat monitor replaces failed replicas.

### Terminal 1

```bash
docker logs -f loadbalancer
```

### Terminal 2

```bash
docker stop server_2
```

### Expected Result

The load balancer should detect the failure and automatically create a replacement server.

Verify using:

```bash
docker ps
```

and

```bash
curl http://localhost:5000/rep
```

---

# Test Case 6: Load Distribution Benchmark

### Objective

Verify that requests are distributed among server replicas.

### Command

```bash
make benchmark
```

### Expected Result

- 10,000 requests are sent to the load balancer.
- Request distribution is displayed.
- Results are saved in:

```
analysis/distribution.csv
```

A bar chart can be generated from this file.

---

# Test Case 7: Scalability Test

### Objective

Evaluate the system as the number of replicas increases.

### Command

```bash
make scale
```

### Expected Result

- The system automatically tests replica counts from 2 to 6.
- Average requests handled per server are calculated.
- Results are saved in:

```
analysis/scaling_results.csv
```

A line chart can be generated from this file.

---

# Summary

The following functionalities were successfully tested:

- Load balancing using consistent hashing
- Dynamic addition of replicas
- Dynamic removal of replicas
- Automatic server failure recovery
- Request distribution across replicas
- Scalability as the number of replicas increases