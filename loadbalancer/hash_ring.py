import random

# Total number of slots in the hash ring
M = 512

# Number of virtual nodes (replicas) per server
K = 9


def H(request_id: int) -> int:
    return (3 * request_id + 19) % M


def PHI(server_id: int, replica_id: int) -> int:
    i, j = server_id, replica_id
    return (5 * i + 7 * j + 31) % M


class ConsistentHashRing:
    def __init__(self):
        # Array representing the hash ring
        self.ring = [None] * M

        # Maps hostname -> server ID
        self.server_ids = {}

        # Stores the slots occupied by each server
        self.server_slots = {}

        # Used to assign unique server IDs
        self._next_id = 0

    def _find_free_slot(self, start_slot):
        slot = start_slot % M
        tries = 0

        while self.ring[slot] is not None and tries < M:
            slot = (slot + 1) % M
            tries += 1

        return slot

    def add_server(self, hostname):
        if hostname in self.server_ids:
            raise ValueError(f"Server '{hostname}' already exists")

        server_id = self._next_id
        self._next_id += 1

        self.server_ids[hostname] = server_id

        occupied_slots = []

        for j in range(K):
            preferred_slot = PHI(server_id, j)
            actual_slot = self._find_free_slot(preferred_slot)

            self.ring[actual_slot] = hostname
            occupied_slots.append(actual_slot)

        self.server_slots[hostname] = occupied_slots

        return server_id

    def remove_server(self, hostname):
        if hostname not in self.server_ids:
            raise ValueError(f"Server '{hostname}' not found")

        for slot in self.server_slots[hostname]:
            self.ring[slot] = None

        del self.server_slots[hostname]
        del self.server_ids[hostname]

    def get_server_for_request(self, request_id):
        if not self.server_ids:
            return None

        slot = H(request_id) % M
        tries = 0

        while self.ring[slot] is None and tries < M:
            slot = (slot + 1) % M
            tries += 1

        return self.ring[slot]

    def hostnames(self):
        return list(self.server_ids.keys())

    def count(self):
        return len(self.server_ids)


def random_request_id():
    return random.randint(100000, 999999)