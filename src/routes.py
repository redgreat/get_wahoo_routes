#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# @author by wangcw @ 2024
# @generate at 2024/11/14 14:34
# comment: 数据获取

import requests
from garmin_fit_sdk import Decoder, Stream
import configparser
import psycopg2
from psycopg2.extras import execute_values
import os
from urllib.parse import urlparse, parse_qs

# 数据库连接定义
config = configparser.ConfigParser()
config.read("../conf/db.cnf")

pg_host = config.get("wahoo", "host")
pg_database = config.get("wahoo", "database")
pg_user = config.get("wahoo", "user")
pg_password = config.get("wahoo", "password")
pg_port = int(config.get("wahoo", "port"))

auth_client_id = config.get("authorization", "client_id")
auth_client_secret = config.get("authorization", "client_secret")
auth_redirect_uri = config.get("authorization", "redirect_uri")
auth_scope = config.get("authorization", "scope")

fit_path_dir = "../fits/"
if not os.path.exists(fit_path_dir):
    os.makedirs(fit_path_dir, exist_ok=True)

# code_url = (f"https://api.wahooligan.com/oauth/authorize?client_id={auth_client_id}"
#             f"&redirect_uri={auth_redirect_uri}&response_type=code"
#             f"&scope=email workouts_read routes_read offline_data user_read")
#
# code_response = requests.get(code_url, allow_redirects=True)

auth_code = 'RgwWzRKcdzHtS2AjwoNvH7NusyhQhnOaZGp6z1jZ60Y'

# Step 3: Exchange authorization code for access token
token_url = 'https://api.wahooligan.com/oauth/token'
token_data = {
    'client_id': auth_client_id,
    'client_secret': auth_client_secret,
    'redirect_uri': auth_redirect_uri,
    'code': auth_code,
    'grant_type': 'authorization_code'
}

token_response = requests.post(token_url, data=token_data)
tokens = token_response.json()
access_token = tokens['access_token']

# Step 5: Use the access token to get routes
routes_url = 'https://api.wahooligan.com/v1/workouts/?page=1&per_page=1'
headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}

ins_workout_fits = """insert into public.workout_fits(workout_summary_id,altitude,distance,
                    enhanced_altitude,enhanced_speed,gps_accuracy,grade,position_lat,position_long,speed,
                    temperature,battery_soc,created_at) values %s;
                    """

del_workout_fits = "delete from public.workout_fits where workout_summary_id = %s;"

ins_workout_summary = ("insert into public.workout_summary(id,workout_id,ascent_accum,distance_accum,"
                       "duration_active_accum,duration_paused_accum,duration_total_accum,speed_avg,"
                       "created_at,updated_at) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
                       "on conflict (id) do update set ascent_accum=excluded.ascent_accum,"
                       "distance_accum=excluded.distance_accum,"
                       "duration_active_accum=excluded.duration_active_accum,"
                       "duration_paused_accum=excluded.duration_paused_accum,"
                       "duration_total_accum=excluded.duration_total_accum,"
                       "speed_avg=excluded.speed_avg,created_at=excluded.created_at,updated_at=excluded.updated_at;")

ins_workout_info = ("insert into public.workout_info(id,starts,minutes,workout_type_id,"
                    "created_at,updated_at) values(%s,%s,%s,%s,%s,%s) on conflict (id) do update set "
                    "starts=excluded.starts,minutes=excluded.minutes,workout_type_id=excluded.workout_type_id,"
                    "created_at=excluded.created_at,updated_at=excluded.updated_at;")


def insert_db(in_sql, in_data):
    try:
        cur = con.cursor()
        cur.execute(in_sql, in_data)
        con.commit()
    except Exception as e:
        print(e)
    finally:
        cur.close()


def parse_fits(in_summary_id, in_file_path):
    try:
        stream = Stream.from_file(in_file_path)
        decoder = Decoder(stream)
        messages, errors = decoder.read()
        record_message = messages.get('record_mesgs')
        cur = con.cursor()
        cur.execute(del_workout_fits, (in_summary_id,))
        con.commit()
        ins_values = []
        for record_fit in record_message:
            ins_value = (in_summary_id, record_fit.get('altitude'), record_fit.get('distance'),
                         record_fit.get('enhanced_altitude'), record_fit.get('enhanced_speed'),
                         record_fit.get('gps_accuracy'), record_fit.get('grade'), record_fit.get('position_lat'),
                         record_fit.get('position_long'), record_fit.get('speed'), record_fit.get('temperature'),
                         record_fit.get('battery_soc'), record_fit.get('timestamp'))
            ins_values.append(ins_value)
        execute_values(cur, ins_workout_fits, ins_values, page_size=1000)
        con.commit()
    except Exception as e:
        print(e)
    finally:
        cur.close()


def parse_files(in_workout_summary_id, in_files):
    try:
        for file in in_files:
            file_url = file.get('url')
            dl_response = requests.get(file_url)
            if dl_response.status_code == 200:
                file_name = os.path.basename(file_url)
                full_file_path = os.path.join(fit_path_dir, file_name)
                with open(full_file_path, 'wb') as fitfile:
                    fitfile.write(dl_response.content)
                parse_fits(in_workout_summary_id, full_file_path)
            else:
                print(f'Failed to download file. Status code: {dl_response.status_code}')
    except Exception as e:
        print(e)


def parse_workout_summary(in_workout_id, in_workout_summary):
    try:
        if in_workout_summary:
            workout_summary_id = in_workout_summary.get('id')
            ascent_accum = in_workout_summary.get('ascent_accum')  # decimal Ascent in meters
            distance_accum = in_workout_summary.get('distance_accum')  # decimal 	Meters
            duration_active_accum = in_workout_summary.get('duration_active_accum')  # decimal 	Seconds
            duration_paused_accum = in_workout_summary.get('duration_paused_accum')  # decimal 	Seconds
            duration_total_accum = in_workout_summary.get('duration_total_accum')  # decimal 	Seconds
            speed_avg = in_workout_summary.get('speed_avg')  # decimal 	Meters/Sec
            summary_created_at = in_workout_summary.get('created_at')
            summary_updated_at = in_workout_summary.get('updated_at')
            summary_data = (workout_summary_id, in_workout_id, ascent_accum, distance_accum, duration_active_accum,
                            duration_paused_accum, duration_total_accum, speed_avg, summary_created_at,
                            summary_updated_at)
            insert_db(ins_workout_summary, summary_data)
            files = in_workout_summary.get('files')
            if files:
                parse_files(workout_summary_id, files)
    except Exception as e:
        print(e)


def parse_workout(in_workouts):
    try:
        if in_workouts:
            for workout in in_workouts:
                workout_id = workout.get('id')
                starts = workout.get('starts')
                minutes = workout.get('minutes')
                workout_type_id = workout.get('workout_type_id')
                created_at = workout.get('created_at')
                updated_at = workout.get('updated_at')
                workout_summary = workout.get('workout_summary')
                info_data = (workout_id, starts, minutes, workout_type_id, created_at, updated_at)
                insert_db(ins_workout_info, info_data)
                parse_workout_summary(workout_id, workout_summary)
    except Exception as e:
        print(e)


con = psycopg2.connect(database=pg_database,
                       user=pg_user,
                       password=pg_password,
                       host=pg_host,
                       port=pg_port)

routes_response = requests.get(routes_url, headers=headers)

if routes_response.status_code == 200:
    routes_data = routes_response.json()
    workouts = routes_data.get('workouts')
    parse_workout(workouts)
else:
    print(f"Error: {routes_response.status_code} - {routes_response.text}")
