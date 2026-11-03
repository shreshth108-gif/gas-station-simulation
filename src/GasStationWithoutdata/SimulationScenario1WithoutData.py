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


class GasStationSimulationScenario1NoData:
    def __init__(self, interArrivalDist, fuelServiceDist, shopTimeDist, paymentServiceDist, p_shop, p_left, p_right):
        self.interArrivalDist = interArrivalDist
        self.fuelServiceDist = fuelServiceDist
        self.shopTimeDist = shopTimeDist
        self.paymentServiceDist = paymentServiceDist
        self.p_shop = p_shop
        self.p_left = p_left
        self.p_right = p_right
        self.pumps = [Pump(pump_id=i + 1, side='Left' if i >= 2 else 'Right') for i in range(4)]

    def can_proceed(self, car):
        preferred_order = [0, 2, 1, 3]  # Prioritize pumps 1, 3, 2, 4 for cars without preference
        # Handle cars with no parking preference by prioritizing furthest pumps
        if car.parkingPreference is None:
            for index in preferred_order:
                pump = self.pumps[index]
                if not pump.is_occupied:
                    return True, pump
            return False, None  # No suitable pump found

        else:  # For cars with a specific parking preference
            for pump in self.pumps:
                if car.parkingPreference == 'Right':
                    if pump.side == 'Right' and not pump.is_occupied:
                        return True, pump

                elif car.parkingPreference == 'Left':
                    if pump.side == 'Left' and not pump.is_occupied:
                        return True, pump

        return False, None

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
        res_shop = SimResults()
        res_payment = SimResults()
        res = SojournTime()
        blocked_cars = deque()

        a = self.interArrivalDist.rvs()
        preference = self.assignParkingPreference(self.p_left, self.p_right)
        c0 = Car(arrivalTime=a + t, parkingPreference=preference)  # first customer
        firstEvent = Event(Event.CAR_ARRIVAL, c0.arrivalTime, c0)
        fes.add(firstEvent)  # schedule first arrival event

        while t < T:
            event = fes.next()
            car = event.car
            t = event.event_time
            res_fuel.registerQueueLength(t, len(queues.fuel_queue))
            res_shop.registerQueueLength(t, len(queues.shop_queue))
            res_payment.registerQueueLength(t, len(queues.payment_queue))

            if event.event_type == Event.CAR_ARRIVAL:
                queues.fuel_queue.append(car)
                proceed, assigned_pump = self.can_proceed(car)
                if proceed:
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
                if random.random() < self.p_shop:
                    fes.add(Event(Event.START_SHOPPING, t, car))
                else:
                    fes.add(Event(Event.START_PAYMENT, t, car))

            elif event.event_type == Event.START_SHOPPING:
                queues.shop_queue.append(car)
                res_shop.registerWaitingTime(0)
                b = self.shopTimeDist.rvs()
                fes.add(Event(Event.END_SHOPPING, t + b, car))

            elif event.event_type == Event.END_SHOPPING:
                queues.shop_queue.remove(car)
                fes.add(Event(Event.START_PAYMENT, t, car))

            elif event.event_type == Event.START_PAYMENT:
                queues.payment_queue.append(car)
                car.paymentArrivalTime = t
                if len(queues.payment_queue) == 1:
                    res_payment.registerWaitingTime(0)
                    b = self.paymentServiceDist.rvs()
                    fes.add(Event(Event.END_PAYMENT, t + b, car))

            elif event.event_type == Event.END_PAYMENT:
                queues.payment_queue.remove(car)
                queues.fuel_queue.remove(car)
                car.pump.release()
                res.registerSojournTime(t - car.systemArrivalTime)
                for car2 in list(blocked_cars):
                    proceed, assigned_pump = self.can_proceed(car2)
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
                if len(queues.payment_queue) > 0:
                    car2 = queues.payment_queue[0]
                    res_payment.registerWaitingTime(t - car2.paymentArrivalTime)
                    b = self.paymentServiceDist.rvs()
                    fes.add(Event(Event.END_PAYMENT, t + b, car2))
        return res_fuel, res_shop, res_payment, res


interArrivalDist = stats.expon(scale=1 / 0.00687)
fuelServiceDist = stats.gamma(a=3.5570, scale=1/0.0129)
shopTimeDist = stats.expon(scale=1 / 0.0145)
paymentServiceDist = stats.uniform(loc=35, scale=20)
p_shop = 0.177
p_left = 0.0886
p_right = 0.0987
simulation = GasStationSimulationScenario1NoData(interArrivalDist, fuelServiceDist, shopTimeDist,
                                        paymentServiceDist, p_shop, p_left, p_right)
res_fuel, res_shop, res_payment, res = simulation.simulate()

print('Fuel Results:\n', res_fuel)
print('Shop Results:\n', res_shop)
print('Payment Results:\n', res_payment)
print(res)


nr_runs = 35000
res_fuelQL = np.zeros(nr_runs)
res_fuelWaits = np.zeros(nr_runs)
res_shopQL = np.zeros(nr_runs)
res_paymentQL = np.zeros(nr_runs)
res_paymentWaits = np.zeros(nr_runs)
res_sojourn = np.zeros(nr_runs)
for i in tqdm(range(nr_runs)):
    simulation = GasStationSimulationScenario1NoData(interArrivalDist, fuelServiceDist, shopTimeDist,
                                            paymentServiceDist, p_shop, p_left, p_right)
    res_fuel, res_shop, res_payment, res = simulation.simulate()
    res_fuelQL[i] = res_fuel.getMeanQueueLength()
    res_fuelWaits[i] = res_fuel.getMeanWaitingTime()
    res_shopQL[i] = res_shop.getMeanQueueLength()
    res_paymentQL[i] = res_payment.getMeanQueueLength()
    res_paymentWaits[i] = res_payment.getMeanWaitingTime()
    res_sojourn[i] = res.getMeanSojournTime()

print(np.var(res_fuelQL), np.var(res_fuelWaits), np.var(res_shopQL), np.var(res_paymentQL), np.var(res_paymentWaits),
      np.var(res_sojourn))

required_runs = (1.96 * np.std(res_fuelQL) / 0.01) ** 2  # replications for a 0.01 half-width on the mean fuel-queue length
print(required_runs)

halfwidth_fuelQL = 1.96 * np.sqrt(np.var(res_fuelQL)/nr_runs)
halfwidth_fuelWaits = 1.96 * np.sqrt(np.var(res_fuelWaits)/nr_runs)
halfwidth_shopQL = 1.96 * np.sqrt(np.var(res_shopQL)/nr_runs)
halfwidth_paymentQL = 1.96 * np.sqrt(np.var(res_paymentQL)/nr_runs)
halfwidth_paymentWaits = 1.96 * np.sqrt(np.var(res_paymentWaits)/nr_runs)
halfwidth_sojourn = 1.96 * np.sqrt(np.var(res_sojourn)/nr_runs)

print(np.mean(res_fuelQL))
print((np.mean(res_fuelQL) - halfwidth_fuelQL, np.mean(res_fuelQL) + halfwidth_fuelQL))

print(np.mean(res_fuelWaits))
print((np.mean(res_fuelWaits) - halfwidth_fuelWaits, np.mean(res_fuelWaits) + halfwidth_fuelWaits))

print(np.mean(res_shopQL))
print((np.mean(res_shopQL) - halfwidth_shopQL, np.mean(res_shopQL) + halfwidth_shopQL))

print(np.mean(res_paymentQL))
print((np.mean(res_paymentQL) - halfwidth_paymentQL, np.mean(res_paymentQL) + halfwidth_paymentQL))

print(np.mean(res_paymentWaits))
print((np.mean(res_paymentWaits) - halfwidth_paymentWaits, np.mean(res_paymentWaits) + halfwidth_paymentWaits))

print(np.mean(res_sojourn))
print((np.mean(res_sojourn) - halfwidth_sojourn, np.mean(res_sojourn) + halfwidth_sojourn))
