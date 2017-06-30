from setuptools import setup

files = ["mos/*"]

setup(name="mos",
      version="0.0.2",
      author="Taylor Romero",
      author_email="taylor@spruce.me",
      packages=['mos'],
      dependency_links=[
          'https://github.com/adafruit/Adafruit_Python_GPIO.git@master#egg=Adafruit-GPIO',
          'https://github.com/adafruit/Adafruit_Python_LED_Backpack.git@master#egg=Adafruit-LED-Backpack'
      ],
      install_requires=[
          'SocketIO-client-2',
          'argparse',
          'Adafruit-GPIO',
          'Adafruit-LED-Backpack'
      ],
      scripts=['bin/mos'])
