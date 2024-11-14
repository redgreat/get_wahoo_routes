#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# @author by wangcw @ 2024
# @generate at 2024/11/14 14:34
# comment: 数据获取

import requests
import fitparse
import configparser
import psycopg2
import os

# 数据库连接定义
config = configparser.ConfigParser()
config.read("../conf/db.cnf")

pg_host = config.get("wahoo", "host")
pg_database = config.get("wahoo", "database")
pg_user = config.get("wahoo", "user")
pg_password = config.get("wahoo", "password")
pg_port = int(config.get("wahoo", "port"))

con = psycopg2.connect(database=pg_database,
                       user=pg_user,
                       password=pg_password,
                       host=pg_host,
                       port=pg_port)

# fit_path = "D:\github\get_wahoo_routes\fits\"

# Replace with your actual credentials
client_id = 'k4YaBCRubf2AES7XmtAMTmDuvMTFifUIyDDvwAN8oUE'
client_secret = '1-mfGRhSzJO3YZEz9A8wfUSaYRGQhOXq1q21t_hmwCM'
redirect_uri = 'https://eadm.wongcw.cn'
authorization_code = 'WuFJ4LXiuETsBH9WdXxZ94ot_gmjFcqgwE4J5t72KW4'  # Obtained from the OAuth2 flow

# Step 3: Exchange authorization code for access token
token_url = 'https://api.wahooligan.com/oauth/token'
token_data = {
    'client_id': client_id,
    'client_secret': client_secret,
    'redirect_uri': redirect_uri,
    'code': authorization_code,
    'grant_type': 'authorization_code'
}

token_response = requests.post(token_url, data=token_data)
tokens = token_response.json()
access_token = tokens['access_token']

# Step 5: Use the access token to get routes
routes_url = 'https://api.wahooligan.com/v1/workouts'
headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}

routes_response = requests.get(routes_url, headers=headers)

ins_workout_fits = ("insert into public.workout_fits(workout_summary_id,altitude,ascent,descent,distance,"
                    "enhanced_altitude,enhanced_speed,gps_accuracy,grade,position_lat,position_long,speed,"
                    "temperature,created_at) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")

# Print routes information
if routes_response.status_code == 200:
    routes_data = routes_response.json()
    workouts = routes_data['workouts']
    for workout in workouts:
        workout_id = workout['id']
        starts = workout['starts']
        minutes = workout['minutes']
        workout_type_id = workout['workout_type_id']
        workout_summary = workout['workout_summary']
        workout_summary_id = workout_summary['id']
        ascent_accum = workout_summary['ascent_accum']  # decimal Ascent in meters
        distance_accum = workout_summary['distance_accum']  # decimal 	Meters
        duration_active_accum = workout_summary['duration_active_accum']  # decimal 	Seconds
        duration_paused_accum = workout_summary['duration_paused_accum']  # decimal 	Seconds
        duration_total_accum = workout_summary['duration_total_accum']  # decimal 	Seconds
        speed_avg = workout_summary['speed_avg']  # decimal 	Meters/Sec
        files = workout_summary['files']
        for file in files:
            file_url = file['url']
            dl_response = requests.get(file_url)
            if dl_response.status_code == 200:
                # file_name = fit_path + os.path.basename(file_url)
                # with open(fit_path, 'wb') as fitfile:
                #     fitfile.write(dl_response.content)
                # 入库
                try:
                    fitparsed = fitparse.FitFile(dl_response)
                    cur = con.cursor()
                    for record in fitparsed.get_messages("record"):
                        for data in record:
                            print(data)
                            # cur.execute(ins_workout_fits,[data])
                    con.commit()
                except Exception as e:
                    print(e)
                finally:
                    if cur:
                        cur.close()

            else:
                print(f'Failed to download file. Status code: {dl_response.status_code}')

        created_at = workout_summary['created_at']
        updated_at = workout_summary['updated_at']
else:
    print(f"Error: {routes_response.status_code} - {routes_response.text}")
