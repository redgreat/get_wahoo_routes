#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# @author by wangcw @ 2024
# @generate at 2024/11/14 15:43
# comment:

import fitparse

# Load the FIT file
fitfile = fitparse.FitFile("../fits/2024-11-14-232358-ELEMNT_BOLT_81D0-131-0.fit")

# Iterate over all messages of type "record"
# (other types include "device_info", "file_creator", "event", etc)
for record in fitfile.get_messages("record"):

    # Records can contain multiple pieces of data (ex: timestamp, latitude, longitude, etc)
    for data in record:
        print(data)
        print("--")
        # Print the name and value of the data (and the units if it has any)
        # if data.units:
        #     print(" * {}: {} ({})".format(data.name, data.value, data.units))
        # else:
        #     print(" * {}: {}".format(data.name, data.value))

    print("---")
