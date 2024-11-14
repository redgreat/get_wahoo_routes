#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# @author by wangcw @ 2024
# @generate at 2024/11/14 15:43
# comment:

from garmin_fit_sdk import Decoder, Stream

stream = Stream.from_file("../fits/2024-11-13-093727-ELEMNT_BOLT_81D0-128-0.fit")
decoder = Decoder(stream)
messages, errors = decoder.read(
    apply_scale_and_offset=True,
    convert_datetimes_to_dates=True,
    convert_types_to_strings=True,
    enable_crc_check=True,
    expand_sub_fields=True,
    expand_components=True,
    merge_heart_rates=True,
    mesg_listener=None
)

print(errors)
print(messages)
