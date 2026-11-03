import heapq

class Event:
    CAR_ARRIVAL = 0
    END_FUELING = 1
    START_SHOPPING = 2
    END_SHOPPING = 3
    START_PAYMENT = 4
    END_PAYMENT = 5

    def __init__(self, event_type, event_time, car=None):
        self.event_type = event_type
        self.event_time = event_time
        self.car = car

    def __lt__(self, other):
        return self.event_time < other.event_time

    def __str__(self):
        return f"{self.event_type} at {self.event_time}"
