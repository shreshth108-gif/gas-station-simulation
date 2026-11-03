from collections import deque

class GasStationQueues:
    def __init__(self):
        self.fuel_queue = deque()
        self.shop_queue = deque()
        self.payment_queue = deque()

