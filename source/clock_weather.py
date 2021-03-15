#!/usr/bin/python3
"""
Example for Vacuum-Fluorescent-Displays (VFD) 
for a clock with weather info
over RPi-serial or USB-serial
"""
__author__      = "Jochen Krapf"
__email__       = "jk@nerd2nerd.org"
__copyright__   = "Copyright 2021, JK"
__license__     = "GPL3"
__version__     = "0.0.2"

import serial
import datetime
import time
import locale
import requests

# =====

VFD_PORTNAME = 'COM5'   # on Windows: 'COMx'; on Linux: '/dev/ttyUSB0' or '/dev/ttyS0'
VFD_BAUDRATE = 9600   # most controllers use 9600 or 19200 baud
VFD_CODEPAGE = 'cp437'   # code page of the display controller e.g. 'ANSI', 'cp437', 'cp858', 'cp1252'   see https://en.wikipedia.org/wiki/Code_page_437
VFD_INIT = b'\x0C\x1F\x58\x04\x1F\x43\x00'   # clear screen, full brightness, cursor off

SYS_LOCALE = 'de_DE.UTF-8'

TEXT_FORMAT_1 = \
    '\x0B' + \
    '{dt:%H:%M:%S} {W_temp:3.0f}°C {W_humidity:3d}%ƒ' + \
    '{dt:%a} {dt:%d}.{W_description:>14.14}'
TEXT_FORMAT_2 = \
    '\x0B' + \
    '{dt:%H:%M:%S} {W_pressure:4d}hPa{W_clouds:3d}≈' + \
    '{dt:%a} {dt:%d}{W_description:>15.15}'
#     12345678901234567890
# 1   23:59:59 -10°C _99%ƒ
# 1   Mo 31._______Bedeckt
# 2   23:59:59 1013hPa_99≈
# 2   Mo 31________Bedeckt
# for datetime format see https://docs.python.org/3/library/datetime.html   {dt:%Y-%m-%d %H:%M:%S}

WEATHER_REQUEST = 'https://api.openweathermap.org/data/2.5/weather?lat=49.801898&lon=9.943015&lang=DE&units=metric&appid=<your api key>'

# =====

if SYS_LOCALE:
    locale.setlocale(locale.LC_ALL, SYS_LOCALE)

# =====

def get_weather_data(data:dict):
    try:
        r = requests.get(WEATHER_REQUEST, timeout=1)
        if r.status_code == 200:
            rj = r.json()
            data['W_temp'] = rj['main']['temp']
            data['W_feels_like'] = rj['main']['feels_like']
            data['W_pressure'] = rj['main']['pressure']
            data['W_humidity'] = rj['main']['humidity']
            data['W_description'] = rj['weather'][0]['description'].replace('Überwiegend ', 'Überw.').replace('Leichter ', 'Leicht.')
            data['W_clouds'] = rj['clouds']['all']
    except:
        print('ERROR on requesting weather data')

# -----

def init_weather_data(data:dict):
    data['W_temp'] = 99.0
    data['W_feels_like'] = 99.0
    data['W_pressure'] = 999
    data['W_humidity'] = 99
    data['W_description'] = 'ERROR'
    data['W_clouds'] = 99

# =====

def main():
    print('VFD started')
    last_second = None
    get_weahter_counter = 0
    data = {}
    init_weather_data(data)

    try:
        tty = serial.Serial(VFD_PORTNAME, VFD_BAUDRATE, write_timeout=0)
        tty.write(VFD_INIT)

        while 1:
            dt = datetime.datetime.now()
            second = dt.second
            if second != last_second:
                last_second = second
                data['dt'] = dt

                get_weahter_counter -= 1
                if get_weahter_counter <= 0:
                    get_weahter_counter = 300   # every 5 minutes
                    get_weather_data(data)

                if (second//4) & 1:   # switch every 4 seconds
                    text = TEXT_FORMAT_1.format(**data)
                else:
                    text = TEXT_FORMAT_2.format(**data)
                tty.write(text.encode(VFD_CODEPAGE))

            time.sleep(0.1)


    except KeyboardInterrupt:
        print('VFD stopped')

    finally:
        if tty:
            tty.close()

# =====

if __name__ == "__main__":
    main()
