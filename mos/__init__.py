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
        {"product_id": 1031020871724, "address": 0x71, "name": 'Bald Fade'},  # 113
        {"product_id": 762876484, "address": 0x72, "name": 'The Regular'},  # 114
        {"product_id": 404513412, "address": 0x73, "name": 'The Signature'},  # 115
        {"product_id": 9813368132, "address": 0x75, "name": 'Clean Up'},  # 117
        {"product_id": 404512112, "address": 0x76, "name": 'Buzzcut'},  # 118
        {"product_id": 404512392, "address": 0x74, "name": 'Head Shave'},  # 116
        {"product_id": 453926320, "address": 0x77, "name": 'Beard Trim'},  # 119
    ],
    [
        {"product_id": 404513644, "address": 0x70, "name": 'Spruced Up Shave'},  # 112
        {"product_id": 404512688, "address": 0x71, "name": 'Young Spruce'},  # 113
        {"product_id": 9813387908, "address": 0x72, "name": 'Wax'},  # 114
        {"product_id": 11825697604, "address": 0x73, "name": 'Beard Tinting'},  # 115
        {"product_id": 11825795204, "address": 0x74, "name": 'Hair Tinting'},  # 116
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
        return
        # socket.disconnect() a bug?? in socket io can't seem to disconnect. just need one socket io instance

    # connect to appointments
    socket = SocketIO('https://appointments.spruce.me', verify=False,
                      hurry_interval_in_seconds=0.5)
    setup_listeners()

    # wait for connections
    socket.wait()


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
    setup_listeners()
    interval()


def setup_listeners():
    global socket

    logger.info('reconnected...')

    socket.on('connect', on_connect)
    socket.on('reconnect', on_reconnect)
    socket.on('disconnect', on_disconnect)
    socket.on('did-book-appointments', did_make_appointment)
    socket.on('did-cancel-appointments', did_make_appointment)
    socket.on('did-cancel-appointments', did_make_appointment)
    socket.on('did-update-appointment', did_make_appointment)


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


            if time["hours"] == 0:
                time = "%d" % time["minutes"]
            elif time["hours"] < 10:
                time = "%dF%d" % (time["hours"], time["minutes"])
            else:
                time = "%dF" % time['hours']

            logger.info(
                'product with id %d has a wait time of %s' % (int(product_id), time))

            # show_colon = True if time["hours"] > 0 else False


            # led.set_colon(show_colon)
            led.print_number_str(time)
            led.write_display()

    logger.info('done setting LEDS')


def error_out():
    logger.info('ERRORING OUT DISPLAYS')
    for product_id in leds:
        led = leds[int(product_id)]
        led.set_colon(False)
        led.print_number_str('----')
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
        error_out()
        connect()
    if socket and socket.connected:
        logger.info('refreshing times')
        refresh_wait_times()
    else:
        logger.error('holy shit not connected to appointments.spruce.me!')
        error_out()
        connect()

    # check wait_times every 30 seconds
    global timer

    if timer is not None:
        timer.cancel()

    timer = Timer(60.0, interval)
    timer.start()
