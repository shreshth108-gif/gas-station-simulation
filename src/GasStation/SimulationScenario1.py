from GasStation.Event import Event
from GasStation.Car import Car
from GasStation.GasStationQueue import GasStationQueues
from GasStation.FES import FES
from GasStation.SimResults import SimResults, SojournTime
from GasStation.FuelPump import Pump
import pandas as pd
from collections import deque


class GasStationSimulationScenario1:
    def __init__(self, file_path):
        data = pd.read_excel(file_path)
        data['Arrival Time'] = (data['Arrival Time'].dt.hour * 3600 +
                                data['Arrival Time'].dt.minute * 60 +
                                data['Arrival Time'].dt.second)
        data['Parking Preference'] = data['Parking Preference'].astype(object).where(pd.notnull(data['Parking Preference']), None)  # object dtype keeps None under pandas 3
        self.data = data
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

    def simulate(self):
        fes = FES()
        queues = GasStationQueues()
        res_fuel = SimResults()
        res_shop = SimResults()
        res_payment = SimResults()
        res = SojournTime()
        blocked_cars = deque()

        for i in range(len(self.data)):
            arrival = self.data.iloc[i]
            car = Car(arrival['Customer'], arrival['Arrival Time'], arrival['Service time Fuel'],
                      arrival['Service time payment'],
                      arrival['Parking Preference'], arrival['Shop time'])
            event = Event(Event.CAR_ARRIVAL, car.arrivalTime, car)
            fes.add(event)

        while not fes.isEmpty():
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
                    end_fueling_time = t + car.serviceTimeFuel
                    fes.add(Event(Event.END_FUELING, end_fueling_time, car))
                else:
                    blocked_cars.append(car)

            elif event.event_type == Event.END_FUELING:
                if car.shopTime > 0:
                    fes.add(Event(Event.START_SHOPPING, t, car))
                else:
                    fes.add(Event(Event.START_PAYMENT, t, car))

            elif event.event_type == Event.START_SHOPPING:
                queues.shop_queue.append(car)
                res_shop.registerWaitingTime(0)
                fes.add(Event(Event.END_SHOPPING, t + car.shopTime, car))

            elif event.event_type == Event.END_SHOPPING:
                queues.shop_queue.remove(car)
                fes.add(Event(Event.START_PAYMENT, t, car))

            elif event.event_type == Event.START_PAYMENT:
                queues.payment_queue.append(car)
                car.paymentArrivalTime = t
                if len(queues.payment_queue) == 1:
                    res_payment.registerWaitingTime(0)
                    fes.add(Event(Event.END_PAYMENT, t + car.serviceTimePayment, car))

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
                        end_fueling_time = t + car2.serviceTimeFuel
                        fes.add(Event(Event.END_FUELING, end_fueling_time, car2))
                    else:
                         break
                if len(queues.payment_queue) > 0:
                    car2 = queues.payment_queue[0]
                    res_payment.registerWaitingTime(t - car2.paymentArrivalTime)
                    fes.add(Event(Event.END_PAYMENT, t + car2.serviceTimePayment, car2))
        return res_fuel, res_shop, res_payment, res


file = '../data/gasstationdata.xlsx'
simulation = GasStationSimulationScenario1(file)
res_fuel, res_shop, res_payment, res = simulation.simulate()

print('Fuel Results:\n', res_fuel)
print('Shop Results:\n', res_shop)
print('Payment Results:\n', res_payment)
print(res)
