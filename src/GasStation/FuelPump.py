class Pump:
    def __init__(self, pump_id, side):
        self.pump_id = pump_id
        self.side = side  # 'left' or 'right'
        self.is_occupied = False
        self.current_car = None  # Track the car at the pump

    def occupy(self, car):
        self.is_occupied = True
        self.current_car = car

    def release(self):
        self.is_occupied = False
        self.current_car = None

    def __str__(self):
        return f"Pump {self.pump_id} ({self.side})"
