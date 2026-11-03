class Car:
    def __init__(self, arrivalTime, serviceTimeFuel=None, serviceTimePayment=None, parkingPreference=None,
                 shopTime=None, pump=None, paymentArrivalTime=None):
        self.arrivalTime = arrivalTime
        self.systemArrivalTime = arrivalTime
        self.serviceTimeFuel = serviceTimeFuel
        self.serviceTimePayment = serviceTimePayment
        self.parkingPreference = parkingPreference
        self.shopTime = shopTime
        self.pump = pump
        self.paymentArrivalTime = paymentArrivalTime

    def __str__(self):
        return f"Car arrived at {self.arrivalTime}: Parked at {self.pump}"