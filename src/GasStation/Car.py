class Car:
    def __init__(self, id, arrivalTime, serviceTimeFuel, serviceTimePayment, parkingPreference=None,
                 shopTime=None, pump=None, paymentArrivalTime=None):
        self.id = id
        self.arrivalTime = arrivalTime
        self.systemArrivalTime = arrivalTime
        self.serviceTimeFuel = serviceTimeFuel
        self.serviceTimePayment = serviceTimePayment
        self.parkingPreference = parkingPreference
        self.shopTime = shopTime
        self.pump = pump
        self.paymentArrivalTime = paymentArrivalTime

    def __str__(self):
        return f"Car {self.id} arrived at {self.arrivalTime}: Parked at {self.pump}"