from bluepy import btle
from threading import Lock

import re
import logging
from utils import retry

log = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)
log.setLevel(logging.DEBUG)


class ApexDesk(object):
  DESK_NAME = re.compile('ADJUST*')
  CHARACTERISTIC_UUID = '0000ffe1-0000-1000-8000-00805f9b34fb'

  COMMANDS = {
    "REQUEST_SETTINGS": "HATSTART",
    "PRESET_A": "HAT008G1",
    "PRESET_B": "HAT009G2",
    "PRESET_C": "HAT010G3",
    "INCREASE": "HAT001AQ",
    "DECREASE": "HAT002BW",
  }

  class InnerScanner(btle.DefaultDelegate):
    def __init__(self, parent):
      self.parent = parent
      super().__init__()

    def handleDiscovery(self, dev, isNewDev, isNewData):
      if isNewDev:
        name = dev.getValueText(9)

        if name and self.parent.DESK_NAME.match(name):
          log.info('Found desk {0}'.format(name))
          self.parent.device_address = dev.addr

  class InnerNotifier(btle.DefaultDelegate):
    HEIGHT_NOTIFICATION_HANDLE = 37
    HEIGHT_REGEX = re.compile(b'(\d+\.?\d*)in\r\n')

    def __init__(self, parent):
      self.parent = parent
      super().__init__()

    def handleNotification(self, handle, data):
      if handle == self.HEIGHT_NOTIFICATION_HANDLE:
        matches = self.HEIGHT_REGEX.match(data)

        if matches:
          self.parent.desk_height = float(matches.group(1))

  def __init__(self, scanning_timeout=20, *args, **kwargs):
    self.lock = Lock()
    self.desk_device = None
    self.desk_height = None
    self.device_address = None
    self.desk_characteristic = None
    self.scanning_timeout = scanning_timeout

    super().__init__(*args, **kwargs)

  @retry(Exception, tries=10, delay=0, backoff=0, logger=log)
  def __discover_address(self):
    scanner = btle.Scanner().withDelegate(self.InnerScanner(parent=self))
    scanner.scan(self.scanning_timeout)

    if not self.device_address:
      raise Exception("Desk was not found")

  def __establish_connection(self):
    self.desk_device = btle.Peripheral(self.device_address).withDelegate(self.InnerNotifier(parent=self))
    log.info('Connected to device {0}'.format(self.desk_device))

    self.desk_characteristic = self.desk_device.getCharacteristics(uuid=self.CHARACTERISTIC_UUID)[0]
    log.info('Found desk characteristic {0}'.format(self.desk_characteristic))

    while True:
      with self.lock:
        self.desk_device.waitForNotifications(1.0)

  def command(self, command):
    with self.lock:
      self.desk_characteristic.write(bytes(self.COMMANDS[command], 'utf-8'))

  def preset_a(self):
    self.command('PRESET_A')

  def preset_b(self):
    self.command('PRESET_B')

  def preset_c(self):
    self.command('PRESET_C')

  def increase(self):
    raise NotImplementedError()

  def decrease(self):
    raise NotImplementedError()

  def request_settings(self):
    raise NotImplementedError()

  def start(self):
    self.__discover_address()
    self.__establish_connection()
