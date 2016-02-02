from socketIO_client import SocketIO, BaseNamespace
from mos.SevenSegmentMock import SevenSegmentMock
from Adafruit_LED_Backpack import SevenSegment
from threading import Timer
import time

import logging

logging.getLogger('requests').setLevel(logging.WARNING)
logging.basicConfig(level=logging.DEBUG)

# our connection
socket = False

# timer
timer = False

# led address
leds_addresses = [
    [],  # mos is 1 or 2 so nothing for 0
    [
        {"product_id": 404511532, "address": 0x70, "name": 'The Ultimate'},
        {"product_id": 419627296, "address": 0x71, "name": 'Style Consult'},
        {"product_id": 404513412, "address": 0x72, "name": 'The Signature'},
        {"product_id": 762876484, "address": 0x73, "name": 'The Regular'},
        {"product_id": 404512112, "address": 0x74, "name": 'The Simple'},
        {"product_id": 404513644, "address": 0x75, "name": 'Spruced Up Shave'},
        {"product_id": 404514000, "address": 0x76, "name": 'Traditional Shave'},
        {"product_id": 404512392, "address": 0x77, "name": 'Head Shave'},
    ],
    [
        {"product_id": 453926320, "address": 0x70, "name": 'Beard Trim'},
        {"product_id": 404510764, "address": 0x71, "name": 'Mustache'},
        {"product_id": 717345668, "address": 0x72, "name": 'Neck Trim'},
        {"product_id": 762920836, "address": 0x73, "name": 'Shampoo'},
        {"product_id": 404512688, "address": 0x74, "name": 'Young Spruce'},
    ],
]

product_ids = []
leds = {}


def start(mos_num=1):
    global socket

    # setup leds
    setup_leds(mos_num=mos_num)

    # check wait_times every 60 seconds
    global timer
    timer = Timer(60.0, interval)
    timer.start()

    # connect to appointments
    socket = SocketIO('https://appointments.spruce.me', verify=False)
    socket.on('connect', on_connect)
    socket.on('did-book-appointments', did_make_appointment)

    socket.wait()


def setup_leds(mos_num=1):
    global product_ids
    global leds

    product_ids = []
    addresses = leds_addresses[mos_num]

    for idx, payload in enumerate(addresses):
        print('setting up product %s on %s' % payload['name'], payload['address'])
        product_ids.append(payload['product_id'])
        address = payload['address']
        led = instantiate_led(address)
        led.begin()
        led.print_float(payload['address'], decimal_digits=0)
        led.write_display()
        leds[payload['product_id']] = led

    print("starting 10 second sleep")
    time.sleep(10)


def on_connect():
    refresh_wait_times()


def did_make_appointment(args):
    refresh_wait_times()


def refresh_wait_times():
    socket.emit('wait-times-in-minutes', product_ids, did_get_wait_times)


def did_get_wait_times(error, wait_times):
    if error is not None:
        print('wait_times_error')
        print(error)
        return

    for product_id, wait_time in wait_times.iteritems():
        led = leds[int(product_id)]
        led.clear()
        time = minutes_to_hours_minutes(wait_time)

        show_colon = True if time["hours"] > 0 else False
        time = "%s%s" % (time['hours'], time['minutes'])
        led.set_colon(show_colon)
        led.print_float(float(time), decimal_digits=0)
        led.write_display()


def instantiate_led(address):
    # return SevenSegmentMock(address=address)
    return SevenSegment.SevenSegment(address=address)


def minutes_to_hours_minutes(minutes):
    time = {"hours": 0, "minutes": 0}
    min = minutes % 60
    hours = (minutes - min) / 60
    time["hours"] = hours
    time["minutes"] = min
    return time


def interval():
    if socket.connected:
        refresh_wait_times()
