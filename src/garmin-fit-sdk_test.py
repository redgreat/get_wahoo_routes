#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# @author by wangcw @ 2024
# @generate at 2024/11/14 15:43
# comment:

from garmin_fit_sdk import Decoder, Stream

stream = Stream.from_file("../fits/2024-11-14-232358-ELEMNT_BOLT_81D0-131-0.fit")
decoder = Decoder(stream)
messages, errors = decoder.read(convert_datetimes_to_dates=False)
record_message = messages.get('record_mesgs')
for record in record_message:
    print(record)

