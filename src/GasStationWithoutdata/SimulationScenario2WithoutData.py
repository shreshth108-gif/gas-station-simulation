from GasStation.Event import Event
from GasStationWithoutdata.Car2 import Car
from GasStation.GasStationQueue import GasStationQueues
from GasStation.FES import FES
from GasStation.SimResults import SimResults, SojournTime
from GasStation.FuelPump import Pump
from scipy import stats
from collections import deque
import numpy as np
import random
from tqdm import tqdm


class GasStationSimulationScenario2NoData:
    def __init__(self, interArrivalDist, fuelServiceDist, paymentServiceDist, p_left, p_right):
        self.interArrivalDist = interArrivalDist
        self.fuelServiceDist = fuelServiceDist
        self.paymentServiceDist = paymentServiceDist
        self.p_left = p_left
        self.p_right = p_right
        self.pumps = [Pump(pump_id=i + 1, side='Left' if i >= 2 else 'Right') for i in range(4)]

    def can_proceed_without_blocking(self, car):
        preferred_order = [0, 2, 1, 3]  # Prioritize pumps 1, 3, 2, 4 for cars without preference
        # Handle cars with no parking preference by prioritizing furthest pumps
        if car.parkingPreference is None:
            for index in preferred_order:
                pump = self.pumps[index]
                if not pump.is_occupied and \
                        not (pump.pump_id == 1 and self.pumps[1].is_occupied) and \
                        not (pump.pump_id == 3 and self.pumps[3].is_occupied):
                    return True, pump
            return False, None  # No suitable pump found
        else:  # For cars with a specific parking preference
            for pump in self.pumps:
                if car.parkingPreference == 'Right':
                    # Not blocked by Pump 2's occupancy when preferring right
                    if pump.side == 'Right' and not pump.is_occupied and not self.pumps[1].is_occupied:
                        return True, pump
                elif car.parkingPreference == 'Left':
                    # Not blocked by Pump 4's occupancy when preferring left
                    if pump.side == 'Left' and not pump.is_occupied and not self.pumps[3].is_occupied:
                        return True, pump
        return False, None

    def can_leave_without_blocking(self, car):
        if car.pump is None:
            return True

        elif car.pump.pump_id == 4:
            if self.pumps[2].is_occupied:
                return False  # The car at Pump 4 is blocked by the car at Pump 3

        elif car.pump.pump_id == 2:
            if self.pumps[0].is_occupied:
                return False  # The car at Pump 2 is blocked by the car at Pump 1

        return True

    def assignParkingPreference(self, p_left, p_right):
        probabilities = [p_left, p_right, 1-p_left-p_right]
        preferences = ['Left', 'Right', None]
        parking_preference = np.random.choice(preferences, p=probabilities)
        return parking_preference

    def simulate(self, T=79200):
        t = 21600
        fes = FES()
        queues = GasStationQueues()
        res_fuel = SimResults()
        res = SojournTime()
        blocked_cars = deque()
        cannot_leave = deque()

        a = self.interArrivalDist.rvs()
        preference = self.assignParkingPreference(self.p_left, self.p_right)
        c0 = Car(arrivalTime=a + t, parkingPreference=preference)  # first customer
        firstEvent = Event(Event.CAR_ARRIVAL, c0.arrivalTime, c0)
        fes.add(firstEvent)  # schedule first arrival event

        while t<T:
            event = fes.next()
            car = event.car
            t = event.event_time
            res_fuel.registerQueueLength(t, len(queues.fuel_queue))

            if event.event_type == Event.CAR_ARRIVAL:
                queues.fuel_queue.append(car)
                proceed, assigned_pump = self.can_proceed_without_blocking(car)
                if proceed and len(blocked_cars) == 0:
                    res_fuel.registerWaitingTime(t - car.arrivalTime)
                    assigned_pump.occupy(car)
                    car.pump = assigned_pump
                    b = self.fuelServiceDist.rvs()
                    end_fueling_time = t + b
                    fes.add(Event(Event.END_FUELING, end_fueling_time, car))
                else:
                    blocked_cars.append(car)
                a = self.interArrivalDist.rvs()
                preference = self.assignParkingPreference(self.p_left, self.p_right)
                c2 = Car(arrivalTime=a + t, parkingPreference=preference)  # create next arrival
                fes.add(Event(Event.CAR_ARRIVAL, c2.arrivalTime, c2))  # schedule next arrival event

            elif event.event_type == Event.END_FUELING:
                b = self.paymentServiceDist.rvs()
                endPaymentTime = t + b
                fes.add(Event(Event.END_PAYMENT, endPaymentTime, car))

            elif event.event_type == Event.END_PAYMENT:
                queues.fuel_queue.remove(car)
                if not self.can_leave_without_blocking(car):
                    cannot_leave.append(car)
                if self.can_leave_without_blocking(car):
                    car.pump.release()
                    res.registerSojournTime(t - car.systemArrivalTime)
                    for car2 in list(cannot_leave):
                        if self.can_leave_without_blocking(car2):
                            cannot_leave.remove(car2)
                            car2.pump.release()
                            res.registerSojournTime(t - car2.systemArrivalTime)
                    for car2 in list(blocked_cars):
                        proceed, assigned_pump = self.can_proceed_without_blocking(car2)
                        if proceed:
                            res_fuel.registerWaitingTime(t - car2.arrivalTime)
                            blocked_cars.remove(car2)
                            assigned_pump.occupy(car2)
                            car2.pump = assigned_pump
                            b = self.fuelServiceDist.rvs()
                            end_fueling_time = t + b
                            fes.add(Event(Event.END_FUELING, end_fueling_time, car2))
                        else:
                            break
        return res_fuel, res


interArrivalDist = stats.expon(scale=1 / 0.00687)
fuelServiceDist = stats.gamma(a=3.5570, scale=1/0.0129)
paymentServiceDist = stats.uniform(loc=35, scale=20)
p_left = 0.0886
p_right = 0.0987
simulation = GasStationSimulationScenario2NoData(interArrivalDist, fuelServiceDist,
                                        paymentServiceDist, p_left, p_right)
res_fuel, res = simulation.simulate()

print('Fuel Results:\n', res_fuel)
print(res)


nr_runs = 35000
res_fuelQL = np.zeros(nr_runs)
res_fuelWaits = np.zeros(nr_runs)
res_sojourn = np.zeros(nr_runs)
for i in tqdm(range(nr_runs)):
    simulation = GasStationSimulationScenario2NoData(interArrivalDist, fuelServiceDist,
                                            paymentServiceDist, p_left, p_right)
    res_fuel, res = simulation.simulate()
    res_fuelQL[i] = res_fuel.getMeanQueueLength()
    res_fuelWaits[i] = res_fuel.getMeanWaitingTime()
    res_sojourn[i] = res.getMeanSojournTime()

print(np.var(res_fuelQL), np.var(res_fuelWaits), np.var(res_sojourn))

required_runs = (1.96 * np.std(res_fuelQL) / 0.01) ** 2  # replications for a 0.01 half-width on the mean fuel-queue length
print(required_runs)

halfwidth_fuelQL = 1.96 * np.sqrt(np.var(res_fuelQL)/nr_runs)
halfwidth_fuelWaits = 1.96 * np.sqrt(np.var(res_fuelWaits)/nr_runs)
halfwidth_sojourn = 1.96 * np.sqrt(np.var(res_sojourn)/nr_runs)

print(np.mean(res_fuelQL))
print((np.mean(res_fuelQL) - halfwidth_fuelQL, np.mean(res_fuelQL) + halfwidth_fuelQL))

print(np.mean(res_fuelWaits))
print((np.mean(res_fuelWaits) - halfwidth_fuelWaits, np.mean(res_fuelWaits) + halfwidth_fuelWaits))

print(np.mean(res_sojourn))
print((np.mean(res_sojourn) - halfwidth_sojourn, np.mean(res_sojourn) + halfwidth_sojourn))