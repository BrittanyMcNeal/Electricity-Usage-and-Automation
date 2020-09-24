import configparser
import datetime
import os
from datetime import date
from twilio.rest import Client

import pandas as pd
from dateutil.relativedelta import relativedelta
from pytz import timezone

from meter_session_manager import MeterSessionManager

# Set Storage Mode:
BLOB_ENABLED = False

# Prepare Secrets
assert os.path.exists("secrets.ini")
key_config = configparser.ConfigParser()
key_config.read("secrets.ini")
assert key_config
username = key_config['CREDENTIALS']['SMART_METER_USERNAME']
password = key_config['CREDENTIALS']['SMART_METER_PASSWORD']

assert username and password, "Could not source USERNAME and PASSWORD!"

# Set Data Files
METER_INFO_DATAFILE = "meter_info.csv"
MONTHLY_TRENDS_DATAFILE = "monthly_trends.csv"
DAILY_TRENDS_DATAFILE = "daily_trends.csv"
INTERVAL_TRENDS_DATAFILE = "interval_trends.csv"
LAST_BILLED_METER_READING_DATAFILE = "last_billed_meter_reading.csv"
LATEST_METER_READING_DATAFILE = "latest_meter_reading.csv"
USAGE_SINCE_LAST_READING_DATAFILE = "usage_since_last_reading.csv"
CURRENT_USAGE_DATAFILE = "current_usage.csv"
PAST_24_HOUR_TREND_DATAFILE = "past_24_hour_trend.csv"
HISTORIC_HOURLY_TREND_DATAFILE = "historic_hourly_trend.csv"

data_files_list = [METER_INFO_DATAFILE,
                   MONTHLY_TRENDS_DATAFILE,
                   DAILY_TRENDS_DATAFILE,
                   INTERVAL_TRENDS_DATAFILE,
                   LAST_BILLED_METER_READING_DATAFILE,
                   LATEST_METER_READING_DATAFILE,
                   USAGE_SINCE_LAST_READING_DATAFILE,
                   CURRENT_USAGE_DATAFILE,
                   PAST_24_HOUR_TREND_DATAFILE,
                   HISTORIC_HOURLY_TREND_DATAFILE]

# Prepare Local Data File Path
data_file_path = os.path.join(os.path.abspath(os.path.curdir), "data_files")
os.makedirs(data_file_path, exist_ok=True)


# Write File to Local
def write_data_to_file_as_pdf(data, file_name):
    try:
        if isinstance(data, dict):
            try:
                df = pd.DataFrame(data, index=[0])
            except:
                df = pd.DataFrame.from_dict(data)
        elif isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            raise NotImplementedError
        local_file_name = os.path.join(data_file_path, file_name)
        df.to_csv(local_file_name, index=False)
    except Exception as e:
        print("Failed to Write Data to File: [{}]".format(file_name))


def send_text_message():
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

    # Your Account SID from twilio.com/console
    account_sid = key_config['TWILIO']['TWILIO_USERNAME']
    # Your Auth Token from twilio.com/console
    auth_token = key_config['TWILIO']['TWILIO_TOKEN']
    client = Client(account_sid, auth_token)

    #hide phone number
    to_phone = key_config['NUMBER']['TO_TELE']
    from_phone = key_config['NUMBER']['FROM_TELE']
    if usage_per_day_so_far < target_usage_per_day:
        body = f"Use more! So far used {round(usage_per_day_so_far, 1)} per day. For next {round(days_remaining, 1)} days need to use {round(target_usage_per_day, 1)} per day."
        message = client.messages.create(to=to_phone, from_=from_phone, body=body)
    else:
        body = f"Use less! So far used {round(usage_per_day_so_far, 1)} per day. For next {round(days_remaining, 1)} days need to use {round(target_usage_per_day, 1)} per day."
        message = client.messages.create(to=to_phone, from_=from_phone, body=body)
    return message

# Read File from Local
def read_data_from_file_as_pdf(file_name):
    try:
        local_file_name = os.path.join(data_file_path, file_name)
        return pd.read_csv(local_file_name)
    except Exception as e:
        print("Failed to Read Data from File: [{}]".format(file_name))
        return None


if __name__ == "__main__":
    try:
        print("#" * 30)
        start_time = datetime.datetime.now(tz=timezone("US/Central"))
        print("Fetch Usage Started At: [{}]".format(start_time))

        msm = MeterSessionManager(username=username, password=password)
        msm.set_auth_keys()
        dashboard_meta = msm.get_dashboard()
        meter_master_info = msm.meter_details
        if meter_master_info:
            meter_info = {
                "ADDRESS": meter_master_info['fullAddress'],
                "METER_NUMBER": meter_master_info['meterNumber'],
                "ESIID": meter_master_info['esiid']
            }
            write_data_to_file_as_pdf(meter_info, METER_INFO_DATAFILE)

        usageData = dashboard_meta.get("usageData")
        interval_usage = list()
        for x in usageData:
            usage_date_time = "{date}{time}".format(date=x['date'], time=x['endtime']).upper()
            usage_date_time = datetime.datetime.strptime(usage_date_time, "%Y-%m-%d %I:%M %p")
            usage = x['consumption']
            interval_usage.append({"USAGE_TIME": usage_date_time, "USAGE": usage})
        if interval_usage:
            write_data_to_file_as_pdf(interval_usage, INTERVAL_TRENDS_DATAFILE)

        monthly_trends = msm.get_monthly_usage_trends(12)
        if monthly_trends:
            write_data_to_file_as_pdf(monthly_trends, MONTHLY_TRENDS_DATAFILE)

        daily_trends = msm.get_daily_usage_trends(45)
        if daily_trends:
            write_data_to_file_as_pdf(daily_trends, DAILY_TRENDS_DATAFILE)

        latest_billed_data = msm.get_latest_billed_reading()
        if latest_billed_data:
            write_data_to_file_as_pdf(latest_billed_data, LAST_BILLED_METER_READING_DATAFILE)

        usage_since_last_on_demand_reading, current_meter_reading = msm.get_on_demand_read()
        if current_meter_reading:
            write_data_to_file_as_pdf(current_meter_reading, LATEST_METER_READING_DATAFILE)
        if usage_since_last_on_demand_reading:
            write_data_to_file_as_pdf(usage_since_last_on_demand_reading, USAGE_SINCE_LAST_READING_DATAFILE)

        current_usage = current_meter_reading["CURRENT_READING"] - latest_billed_data["LAST_BILLED_READING"]
        current_usage = {"CURRENT_CYCLE_USAGE": current_usage}
        if current_usage:
            write_data_to_file_as_pdf(current_usage, CURRENT_USAGE_DATAFILE)

        if os.path.exists(os.path.join(data_file_path, PAST_24_HOUR_TREND_DATAFILE)):
            past_24_hour_trend_df = read_data_from_file_as_pdf(PAST_24_HOUR_TREND_DATAFILE)
            trend_start_time = start_time - datetime.timedelta(hours=24)
            trend_start_time = trend_start_time.replace(tzinfo=None)
            past_24_hour_trend_df['READING_TIME'] = past_24_hour_trend_df['READING_TIME'].astype('datetime64[ns]')
            past_24_hour_trend_df = past_24_hour_trend_df[past_24_hour_trend_df["READING_TIME"] >= trend_start_time]
            past_24_hour_trend_dict = past_24_hour_trend_df.to_dict(orient='list')
            past_24_hour_trend_dict["READING_TIME"] = [x.to_pydatetime() for x in
                                                       past_24_hour_trend_dict["READING_TIME"]]
        else:
            past_24_hour_trend_dict = {"READING_TIME": list(), "METER_READING": list()}

        if current_meter_reading["CURRENT_READING_TIME"] not in past_24_hour_trend_dict["READING_TIME"]:
            past_24_hour_trend_dict["READING_TIME"].append(current_meter_reading["CURRENT_READING_TIME"])
            past_24_hour_trend_dict["METER_READING"].append(current_meter_reading["CURRENT_READING"])
            write_data_to_file_as_pdf(past_24_hour_trend_dict, PAST_24_HOUR_TREND_DATAFILE)

        if os.path.exists(os.path.join(data_file_path, HISTORIC_HOURLY_TREND_DATAFILE)):
            historic_hourly_trend_df = read_data_from_file_as_pdf(HISTORIC_HOURLY_TREND_DATAFILE)
            historic_hourly_trend_df['READING_TIME'] = historic_hourly_trend_df['READING_TIME'].astype('datetime64[ns]')
            historic_hourly_trend_dict = historic_hourly_trend_df.to_dict(orient='list')
            historic_hourly_trend_dict["READING_TIME"] = [x.to_pydatetime() for x in
                                                       historic_hourly_trend_dict["READING_TIME"]]
        else:
            historic_hourly_trend_dict = {"READING_TIME": list(), "METER_READING": list()}

        if current_meter_reading["CURRENT_READING_TIME"] not in historic_hourly_trend_dict["READING_TIME"]:
            historic_hourly_trend_dict["READING_TIME"].append(current_meter_reading["CURRENT_READING_TIME"])
            historic_hourly_trend_dict["METER_READING"].append(current_meter_reading["CURRENT_READING"])
            write_data_to_file_as_pdf(historic_hourly_trend_dict, HISTORIC_HOURLY_TREND_DATAFILE)

        print("-" * 30)
        print(read_data_from_file_as_pdf(PAST_24_HOUR_TREND_DATAFILE))
        print("\n")
        print("-" * 30)
        print(read_data_from_file_as_pdf(CURRENT_USAGE_DATAFILE))
        print("-" * 30)
        end_time = datetime.datetime.now(tz=timezone("US/Central"))
        print("Fetch Usage Ended At: [{}]".format(end_time))
        elapsed_time = relativedelta(end_time, start_time)
        print("Time Taken: [{}]Minutes [{}]Seconds".format(elapsed_time.minutes, elapsed_time.seconds))
        print("#" * 30)
        print("\n")

        send_text_message()
    except Exception as e:
        print(e)
