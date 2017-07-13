from socketIO_client import SocketIO, BaseNamespace
from mos.SevenSegmentMock import SevenSegmentMock
from Adafruit_LED_Backpack import SevenSegment
from threading import Timer
import time

import logging
import sys

logging.getLogger('requests').setLevel(logging.WARNING)
logging.basicConfig(level=logging.WARNING)

# logging
logger = logging.getLogger('mos')
logger.setLevel(logging.INFO)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

# our connection
socket = None

# timer
timer = None

# led address
leds_addresses = [
    [],  # mos is 1 or 2 so nothing for 0
    [
        {"product_id": 404511532, "address": 0x70, "name": 'The Ultimate'},  # 112
        {"product_id": 419627296, "address": 0x71, "name": 'Style Consult'},  # 113
        {"product_id": 404513412, "address": 0x72, "name": 'The Signature'},  # 114
        {"product_id": 762876484, "address": 0x73, "name": 'The Regular'},  # 115
        {"product_id": 404512112, "address": 0x74, "name": 'The Simple'},  # 116
        {"product_id": 404513644, "address": 0x75, "name": 'Spruced Up Shave'},  # 117
        {"product_id": 404514000, "address": 0x76, "name": 'Traditional Shave'},  # 118
        {"product_id": 404512392, "address": 0x77, "name": 'Head Shave'},  # 119
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
refresh_count = 0


def start(mos_num=1, test_mode=False):
    # setup leds
    setup_leds(mos_num=mos_num, test_mode=test_mode)

    # connect
    interval()


def connect():
    global socket

    if socket is not None:
        socket.disconnect()

    # connect to appointments
    socket = SocketIO('https://appointments.spruce.me', verify=False, transports=['websocket'],
                      hurry_interval_in_seconds=0.5)
    socket.on('connect', on_connect)
    socket.on('reconnect', on_reconnect)
    socket.on('disconnect', on_disconnect)
    socket.on('did-book-appointments', did_make_appointment)
    socket.on('did-cancel-appointments', did_make_appointment)
    socket.on('did-cancel-appointments', did_make_appointment)
    socket.on('did-update-appointment', did_make_appointment)

    count = 0

    # wait for connections
    while True:
        socket.wait(seconds=1)
        count += 1
        logger.info('wait count %d', count)


def setup_leds(mos_num=1, test_mode=False):
    global product_ids
    global leds

    product_ids = []
    addresses = leds_addresses[mos_num]

    for idx, payload in enumerate(addresses):
        logger.info('setting up product %s on %d' % (payload['name'], payload['address']))
        product_ids.append(payload['product_id'])
        address = payload['address']
        try:
            led = instantiate_led(address, test_mode=test_mode)
            led.begin()
            led.print_float(payload['address'], decimal_digits=0)
            led.write_display()
            leds[payload['product_id']] = led
        except IOError as e:
            logger.error("failed to connect to led at %d" % (address))
            logger.exception(e)
        except Exception as e:
            logger.error("failed to connect to led at %d" % (address))
            logger.exception(e)

    logger.info("starting 5 second sleep")
    time.sleep(5)
    logger.info('*yawn* awake again')


def on_disconnect():
    logger.error('SOCKETS DISCONNECTED')
    error_out()
    interval()


def on_connect():
    interval()


def on_reconnect():
    logger.info('reconnected...')
    interval()


def did_make_appointment(args):
    interval()


def refresh_wait_times():
    global refresh_count
    refresh_count -= 1
    socket.emit('wait-times-in-minutes', product_ids, did_get_wait_times)


def did_get_wait_times(error, wait_times):
    if error is not None:
        logger.error('wait_times_error')
        logger.error(error)
        return

    global refresh_count

    refresh_count = 0

    logger.info('got wait times, setting LEDS')

    for product_id, wait_time in wait_times.iteritems():
        if int(product_id) in leds:
            led = leds[int(product_id)]
            led.clear()
            time = minutes_to_hours_minutes(wait_time)

            logger.info(
                'product with id %d has a wait time of %d:%02d' % (int(product_id), time['hours'], time['minutes']))

            show_colon = True if time["hours"] > 0 else False
            time = "%d%02d" % (time['hours'], time['minutes'])
            led.set_colon(show_colon)
            led.print_float(float(time), decimal_digits=0)
            led.write_display()

    logger.info('done setting LEDS')


def error_out():
    for product_id in leds:
        led = leds[int(product_id)]
        led.clear()
        led.write_display()


def instantiate_led(address, test_mode=False):
    if test_mode:
        return SevenSegmentMock(address=address)

    display = SevenSegment.SevenSegment(address=address)
    display._device._logger.setLevel(logging.WARNING)
    return display


def minutes_to_hours_minutes(minutes):
    time = {"hours": 0, "minutes": 0}
    min = minutes % 60
    hours = (minutes - min) / 60
    time["hours"] = hours
    time["minutes"] = min
    return time


def interval():
    logger.info('heartbeat')

    global refresh_count

    logger.error('test %d' % refresh_count)

    if refresh_count > 1:
        logger.error('holy shit not connected to appointments.spruce.me!')
        connect()
        error_out()
    if socket and socket.connected:
        logger.info('refreshing times')
        refresh_wait_times()
    else:
        logger.error('holy shit not connected to appointments.spruce.me!')
        connect()
        error_out()

    # check wait_times every 30 seconds
    global timer

    if timer is not None:
        timer.cancel()

    timer = Timer(60.0, interval)
    timer.start()
