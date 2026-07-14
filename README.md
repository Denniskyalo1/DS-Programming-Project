# Distributed Systems Programming Project

## Group Members

- Dennis Kyalo - 158270
- Larry Seme - 169002
- Timothy Muigai - 150320
- Bill Ritchie - 163362

---

## Project Overview

This project implements a scalable distributed system using a custom load balancer based on Consistent Hashing. The load balancer dynamically distributes incoming client requests across multiple backend server replicas running inside Docker containers.

The system supports:

- Dynamic addition of server replicas
- Dynamic removal of server replicas
- Consistent Hashing for request routing
- Automatic failure detection using heartbeat monitoring
- Automatic recovery by spawning replacement containers
- Experimental performance evaluation

---

## Project Structure

```
DS-Programming-Project/
│
├── server/
│   ├── app.py
│   └── Dockerfile
│
├── loadbalancer/
│   ├── app.py
│   ├── hash_ring.py
│   └── Dockerfile
│
├── analysis/
│   ├── benchmark.py
│   ├── scale_test.py
│   ├── distribution.csv
│   └── scaling_results.csv
│
├── docker-compose.yml
├── Makefile
└── README.md
```

---

## Technologies Used

- Python 3.11
- Flask
- Docker
- Docker Compose
- Requests
- Consistent Hashing
- Make

---

## Building the Project

Build Docker images:

```bash
make build
```

---

## Running the System

Start the load balancer:

```bash
make run
```

Check running containers:

```bash
docker ps
```

---

## Stopping the System

```bash
make stop
```

To remove all containers:

```bash
make clean
```

---

## API Endpoints

### View replicas

```
GET /rep
```

Example:

```bash
curl http://localhost:5000/rep
```

---

### Add replicas

```
POST /add
```

Example:

```bash
curl -X POST http://localhost:5000/add \
-H "Content-Type: application/json" \
-d '{"n":1,"hostnames":["server_4"]}'
```

---

### Remove replicas

```
DELETE /rm
```

Example:

```bash
curl -X DELETE http://localhost:5000/rm \
-H "Content-Type: application/json" \
-d '{"n":1,"hostnames":["server_4"]}'
```

---

### Access application

```
GET /home
```

Example:

```bash
curl http://localhost:5000/home
```

---

## Performance Analysis

Two benchmark programs were developed.

### benchmark.py

Measures request distribution across server replicas after sending 10,000 requests.

Run:

```bash
make benchmark
```

---

### scale_test.py

Measures request distribution while varying the number of replicas.

Run:

```bash
make scale
```

---

## Fault Tolerance

The load balancer continuously monitors backend replicas using heartbeat requests.

If a server fails:

1. The failed replica is detected.
2. The server is removed from the hash ring.
3. The failed Docker container is deleted.
4. A replacement server is automatically launched.
5. The replacement is added back into the hash ring.

This allows the system to continue serving client requests without manual intervention.

---

## Screenshots

The final report includes screenshots demonstrating:

- Running containers
- Request distribution
- Adding replicas
- Removing replicas
- Automatic recovery
- Performance graphs

---
