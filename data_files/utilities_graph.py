import pandas as pd
from datetime import date
import datetime
from twilio.rest import Client
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.dates as mdates


# get date of cycle start and meter reading at that time
cycle_begin_df = pd.read_csv("data_files/last_billed_meter_reading.csv")
date_cycle_start = pd.to_datetime(cycle_begin_df['LAST_BILLED_DATE'])[0]
meter_read_start = cycle_begin_df['LAST_BILLED_READING'][0]

# get current reading date and current meter reading
today_reading_df = pd.read_csv("data_files/latest_meter_reading.csv")
date_read_current = pd.to_datetime(today_reading_df['CURRENT_READING_TIME'])[0]
meter_read_current = today_reading_df['CURRENT_READING'][0]

# get billing cycle csv and convert to dates
billing_dates_df = pd.read_csv("data_files/End_Date.csv")
billing_dates_df['Date'] = pd.to_datetime(billing_dates_df['Date'])

# get date of cycle end by looking up the cycle start date in our CSV, then getting the next date
start_index = billing_dates_df['Date'].tolist().index(date_cycle_start)
date_cycle_end = billing_dates_df['Date'][start_index + 1]

# calculate how far we are in the billing cycle and time left
days_passed = (date_read_current - date_cycle_start) / datetime.timedelta(days=1)
days_remaining = (date_cycle_end - date_read_current) / datetime.timedelta(days=1)

usage_so_far = meter_read_current - meter_read_start
target_usage = 1000
left_to_use = target_usage - usage_so_far
usage_per_day_so_far = usage_so_far / days_passed
target_usage_per_day = left_to_use / days_remaining

print("Cycle Start: " + str(date_cycle_start))
print("Cycle End: " + str(date_cycle_end))
print("Today: " + str(date_read_current))
print("Days Passed: " + str(days_passed))
print("Days Remaining: " + str(days_remaining))
print("Usage so far: " + str(usage_so_far)) 
print("Usage per day so far: " + str(usage_per_day_so_far))
print("Target usage for the rest of the cycle: " + str(target_usage_per_day))

# make a series with dates from the start of the billing cycle to the end of the billing cycle (one row per day)
energy_time = pd.date_range(start=date_cycle_start, end=date_cycle_end)

# turn above into a dataframe
target_df = energy_time.to_frame().reset_index()

# add column of our target daily usage all month (1000 / (length of date series))
target_df['target'] = 1000 / len(energy_time)
target_df.columns = ["DAILY_DATE", "JUNK_COLUMN", "TARGET"]
target_df.drop(columns=['JUNK_COLUMN'], inplace=True)

trends_use = pd.read_csv("data_files/daily_trends.csv")
trends_use['DAILY_DATE'] = pd.to_datetime(trends_use['DAILY_DATE'])

# Maybe done: merge your two dataframes together, keeping only the rows in your first dataframe
trend_target = target_df.merge(trends_use, how='left')
trend_target['cum_sum_TARGET'] = trend_target['TARGET'].cumsum()
trend_target['cum_sum'] = trend_target['USAGE'].cumsum()


print(trend_target)

# TODO: plot merged dataframe
fig, ax = plt.subplots(figsize=(12, 12))
#trend_target.plot(ax=ax)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
sns.lineplot(trend_target['DAILY_DATE'], trend_target['cum_sum'], color='hotpink')
sns.lineplot(trend_target['DAILY_DATE'], trend_target['cum_sum_TARGET'], color='teal')

plt.xlabel("DAILY_DATE", labelpad=15)
plt.ylabel("cum_sum", labelpad=15)

# # TODO: add a line showing cumulative target usage
plt.title("Energy Usage", y=1.02, fontsize=22)
plt.show()



