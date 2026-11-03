import pandas as pd
from numpy import random, arange, sqrt, linspace, sort, cumsum
from datetime import datetime
import matplotlib.pyplot as plt
from statsmodels.distributions.empirical_distribution import ECDF
from scipy import stats
from sklearn.mixture import GaussianMixture

rng = random.default_rng() # The random number generator

file = '../data/gasstationdata.xlsx'

df = pd.read_excel(file, index_col="Customer", parse_dates=True)
df = df.drop("Unnamed: 0", axis=1)
begin_of_day = datetime.strptime("2024-02-01 06:00:00", "%Y-%m-%d %H:%M:%S")

df["Inter_arrival_time"] = df["Arrival Time"].diff()
df.loc[0, "Inter_arrival_time"] = df.loc[0, "Arrival Time"] - begin_of_day

df["Inter_arrival_time"] = df["Inter_arrival_time"].dt.total_seconds()
interArrivalTimes = df["Inter_arrival_time"].values
paymentTimes = df["Service time payment"].values
fuelTimes = df["Service time Fuel"].values

randomSample = rng.choice(paymentTimes, 300, replace=True)

plt.figure()
plt.hist(paymentTimes, bins=20, rwidth=0.8)
plt.show()

uniformDist = stats.uniform(loc=min(paymentTimes), scale=max(paymentTimes)-min(paymentTimes))

ecdf = ECDF(randomSample)
plt.figure()
plt.step(ecdf.x, ecdf.y, color='blue', where='post')
xs = arange(min(randomSample), max(randomSample), 0.1)
plt.plot(xs, uniformDist.cdf(xs), color='red')
plt.legend(['Empirical CDF', 'Theoretical CDF'])
plt.show()

tst1 = stats.kstest(randomSample, uniformDist.cdf)
print(tst1)


plt.figure()
plt.hist(fuelTimes, bins=20, rwidth=0.8)
plt.show()