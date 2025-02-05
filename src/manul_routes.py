#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# @author by wangcw @ 2024
# @generate at 2024/11/14 14:34
# comment: 手动上传定位数据

from garmin_fit_sdk import Decoder, Stream
import configparser
import psycopg2
from psycopg2.extras import execute_values
import os
from datetime import datetime
import io

# 数据库连接定义
config = configparser.ConfigParser()
config.read("../conf/db.cnf")

pg_host = config.get("wahoo", "host")
pg_database = config.get("wahoo", "database")
pg_user = config.get("wahoo", "user")
pg_password = config.get("wahoo", "password")
pg_port = int(config.get("wahoo", "port"))

fit_path_dir = "../fits/"
if not os.path.exists(fit_path_dir):
    os.makedirs(fit_path_dir, exist_ok=True)

ins_workout_fits = """insert into public.workout_fits(workout_summary_id,altitude,distance,enhanced_altitude,
                    enhanced_speed,gps_accuracy,grade,position_lat,position_long,speed,temperature,battery_soc,
                    created_at) values %s;
                    """

ins_workout_imps = """insert into public.workout_imps(file_name) values (%s);"""

sel_workout_imps = """select id from public.workout_imps where file_name = %s;"""


def iso_formater(date_str):
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except ValueError:
        return None


def insert_db(in_sql, in_data):
    try:
        cur = con.cursor()
        cur.execute(in_sql, in_data)
        con.commit()
    except Exception as e:
        print(e)
    finally:
        cur.close()


def parse_files(in_filename, in_file_path):
    try:
        with open(in_file_path, 'rb') as file:
            file_content = file.read()
            file_object = io.BytesIO(file_content)
            stream = Stream.from_bytes_io(file_object)
            decoder = Decoder(stream)
            messages, errors = decoder.read()
            record_message = messages.get('record_mesgs')
            if record_message:
                with con.cursor() as cur:
                    cur.execute(sel_workout_imps, (in_filename,))
                    file_id = cur.fetchone()
                    ins_values = [
                        (file_id, record_fit.get('altitude'), record_fit.get('distance'),
                         record_fit.get('enhanced_altitude'), record_fit.get('enhanced_speed'),
                         record_fit.get('gps_accuracy'), record_fit.get('grade'), record_fit.get('position_lat'),
                         record_fit.get('position_long'), record_fit.get('speed'), record_fit.get('temperature'),
                         record_fit.get('battery_soc'), record_fit.get('timestamp'))
                        for record_fit in record_message
                    ]
                    execute_values(cur, ins_workout_fits, ins_values)
                    con.commit()
    except Exception as e:
        print(f"Error parsing FIT file: {e}")


con = psycopg2.connect(database=pg_database,
                       user=pg_user,
                       password=pg_password,
                       host=pg_host,
                       port=pg_port)

# 遍历指定文件夹内的所有 .fit 文件
for filename in os.listdir(fit_path_dir):
    if filename.endswith(".fit"):
        cur = con.cursor()
        cur.execute(sel_workout_imps, (filename,))
        file_exists = cur.fetchone()
        cur.close()
        if not file_exists:
            file_path = os.path.join(fit_path_dir, filename)
            print(f"Processing file: {file_path}")
            insert_db(ins_workout_imps, (filename,))
            parse_files(filename, file_path)
con.close()
