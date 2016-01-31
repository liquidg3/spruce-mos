from distutils.core import setup

files = ["mos/*"]

setup(name="mos",
      version="0.0.1",
      author="Taylor Romero",
      author_email="taylor@spruce.me",
      packages=['mos'],
      install_requires=[
          'SocketIO-client',
          'argparse',
          'git+https://github.com/adafruit/Adafruit_Python_GPIO.git@master',
          'git+https://github.com/adafruit/Adafruit_Python_LED_Backpack.git@master'
      ],
      scripts=['bin/mos'])
