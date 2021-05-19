""" 
    NFC Tag Sensor Interface
    Allows tracking of specific NFC
    tags and reading data from them 
"""
import time
import json
import redis
from . import NAMESPACE
from mudpi.utils import decode_event_data
from mudpi.extensions import BaseInterface
from mudpi.extensions.sensor import Sensor
from mudpi.logger.Logger import Logger, LOG_LEVEL
from mudpi.exceptions import MudPiError, ConfigError


class Interface(BaseInterface):

    # Override the update interval due to event handling
    update_interval = 1

    # Duration tracking
    _duration_start = time.perf_counter()

    def load(self, config):
        """ Load nfc sensor component from configs """
        sensor = NFCSensor(self.mudpi, config)
        if sensor:
            self.add_component(sensor)

        ##### DEBUG TESTS ######
        print(dir(self))
        print("MANAGER")
        print(self.extension.manager)
        ######
        
        self.extension.manager.register_component_actions('unlock', action='unlock')
        self.extension.manager.register_component_actions('lock', action='lock')
        return True

    def validate(self, config):
        """ Validate the redis sensor config """
        if not isinstance(config, list):
            config = [config]

        for conf in config:
            if not conf.get('key'):
                raise ConfigError('Missing `key` in nfc sensor config.')

            _tag_uid = conf.get('tag_uid')
            _tag_id = conf.get('tag_id')
            if not any([_tag_uid, _tag_id]):
                raise ConfigError('A tag_id or tag_uid must be provided.')

            if conf.get('default_records'):
                for record in conf['default_records']:
                    if record.get('data') is None:
                        raise ConfigError('A record in default_records is missing the `data` property.')


        return config


class NFCSensor(Sensor):
    """ NFC Tag Sensor
        Returns readings for a NFC tag
    """

    """ Properties """
    @property
    def id(self):
        """ Return a unique id for the component """
        return self.config['key']

    @property
    def name(self):
        """ Return the display name of the component """
        return self.config.get('name') or f"{self.id.replace('_', ' ').title()}"

    @property
    def serial(self):
        """ Return tag serial id """
        return self.config.get('tag_id', None)

    @property
    def uid(self):
        """ Return tag uuid """
        return self.config.get('tag_uid', None)
    
    @property
    def state(self):
        """ Return the state of the component (from memory, no IO!) """
        _state = {
            "tag_id": self.serial,
            "tag_uid": self.uid,
            "capacity": self.capacity,
            "used_capacity": self.used_capacity,
            "writeable": self.writeable,
            "readable": self.readable,
            "is_present": self.is_present,
            "scan_count": self.scan_count
        }
        if self.ndef: 
            _state['ndef'] = self.ndef
        if self.count: 
            # Count from the card data
            _state['count'] = self.count
        if self.last_scan: 
            _state['last_scan'] = self.last_scan
        if self.last_reader: 
            _state['last_reader'] = self.last_reader
        if self.security_check: 
            _state['security_check'] = self.security_check
        return _state

    @property
    def classifier(self):
        """ Classification further describing it, effects the data formatting """
        return 'general'

    @property
    def topic(self):
        """ Return the topic to listen on for event sensors """
        return str(self.config.get('topic', f'{NAMESPACE}/{self.id}'))

    @property
    def capacity(self):
        """ Return the total capacity of the tag """
        return int(self._capacity)

    @property
    def used_capacity(self):
        """ Return the used capacity of the tag """
        return int(self._used_capacity)

    @property
    def count(self):
        """ Return the scan count from tag data (requires tracking enabled)"""
        return int(self._count)

    @property
    def last_scan(self):
        """ Return the scan last_scan of the tag (requires tracking enabled)"""
        return self._last_scan

    @property
    def last_reader(self):
        """ Return the last reader tag was scanned at """
        return self._last_reader

    @property
    def scan_count(self):
        """ Number of times scanned - tracked by system """
        return int(self._scan_count)

    @property
    def ndef(self):
        """ Return any ndef records """
        return self._ndef

    @property
    def is_present(self):
        """ Return if card is current present """
        return self._present

    @property
    def security(self):
        """ Set to level of desired security checks for the tag 
            0 = Disabled
            1 = Alerts
            2 = Card Locking
        """
        return self.config.get('security', 0)

    @property
    def locked(self):
        """ Return if card is security locked """
        return self._locked

    @property
    def security_check(self):
        """ Return security message if there is one """
        return self._security_check


    """ Methods """
    def init(self):
        """ Setup the tag """
        self._capacity = 0
        self._used_capacity = 0
        self._readable = True
        self._writeable = True
        self._count = 0
        self._scan_count = 0
        self._last_scan = None
        self._last_reader = None
        self._ndef = []
        self.locked = False
        self._security_check = ''
        self._present = False

        # Used for onetime subscribe
        _listening = False

        # For duration tracking
        self._duration_start = time.perf_counter()

        if self.mudpi.is_prepared:
            if not self._listening:
                self.mudpi.events.subscribe(NAMESPACE, self.handle_event)
                self.mudpi.events.subscribe(self.topic, self.handle_event) # subscribe for personal events
                self._listening = True

        return True


    def handle_event(self, event):
        """ Process event data for the NFC tag """
        _event_data = decode_event_data(event)

        if _event_data == self._last_event:
            # Event already handled
            return

        self._last_event = _event_data

        if self.serial:
            if _event_data['tag_id'] != self.serial:
                return

        if self.uid:
            if _event_data['tag_uid'] != self.uid:
                return

        if self.locked:
            Logger.log(
                LOG_LEVEL["warning"],
                f'Tag {self.name} Scanned. This card has been locked for security.'
            )
            return

        if _event_data.get('event'):
            try:
                if _event_data['event'] == 'NFCTagScanned':
                    self._scan_count += 1
                    self.update_tag(_event_data)
                    Logger.log(
                        LOG_LEVEL["debug"],
                        f'Tag {self.name} Scanned'
                    )
                elif _event_data['event'] == 'NFCNewTagScanned':
                    self._scan_count += 1
                    self.update_tag(_event_data)
                    Logger.log(
                        LOG_LEVEL["debug"],
                        f'Tag {self.name} Scanned for First Time'
                    )
                elif _event_data['event'] == 'NFCTagRemoved':
                    self.update_tag(_event_data)
                    Logger.log(
                        LOG_LEVEL["debug"],
                        f'Tag {self.name} Removed'
                    )
                elif _event_data['event'] == 'NFCTagUIDMismatch':
                    self.update_tag(_event_data)
                    if self.security > 0:
                        self._security_check = 'UID Mismatch'
                        if self.security > 1:
                            self._locked = True
                        Logger.log(
                            LOG_LEVEL["warning"],
                            f'Security Warning: Tag {self.name} UID Mismatches Saved One'
                        )
                elif _event_data['event'] == 'NFCTagUIDMissing':
                    self.update_tag(_event_data)
                    if self.security > 0:
                        self._security_check = 'UID Missing'
                        Logger.log(
                            LOG_LEVEL["debug"],
                            f'Tag {self.name} UID Missing on Tag'
                        )
                elif _event_data['event'] == 'NFCDuplicateUID':
                    self.update_tag(_event_data)
                    if self.security > 0:
                        self._security_check = 'Duplicate UID'
                        if self.security > 1:
                            self._locked = True
                        Logger.log(
                            LOG_LEVEL["debug"],
                            f'Tag {self.name} has UID found on multiple tags!'
                        )
                elif _event_data['event'] == 'NFCNewUIDCreated':
                    self.update_tag(_event_data)
                    Logger.log(
                        LOG_LEVEL["debug"],
                        f'New UID created for tag {self.name}'
                    )
            except:
                Logger.log(
                    LOG_LEVEL["info"],
                    f"Error Decoding Event for Sequence {self.id}"
                )

    def unlock(self):
        """ Unlock the card """
        self._locked = False

    def lock(self):
        """ lock the card """
        self._locked = True

    def update_tag(self, data):
        """ Update the tag sensor with data from a scan event """
        if data.get('reader_id'):
            self._last_reader = data['reader_id']

        # The key is also the reader that fired the event
        if data.get('key'):
            pass
            # self._last_reader = data['key']

        if data.get('updated_at'):
            self._last_scan = data['updated_at']

        if data.get('capacity'):
            self._capacity = data['capacity']

        if data.get('used_capacity'):
            self._used_capacity = data['used_capacity']

        if data.get('writeable'):
            self._writeable = data['writeable']

        if data.get('readable'):
            self._readable = data['readable']

        if data.get('count'):
            self._count = data['count']

        if data.get('ndef'):
            self._ndef = data['ndef']

        return self