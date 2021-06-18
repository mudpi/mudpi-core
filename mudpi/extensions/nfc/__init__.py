""" 
    NFC Extension
    Allows reading and writing to
    NFC cards and tags.
"""
import nfc
import ndef
import time
import datetime
import threading
from uuid import uuid4
from mudpi.workers import Worker
from mudpi.extensions import BaseExtension
from mudpi.logger.Logger import Logger, LOG_LEVEL
from mudpi.constants import FONT_RESET, FONT_CYAN


NAMESPACE = 'nfc'
TYPE_TEXT = ndef.TextRecord().type
TYPE_URI = ndef.UriRecord().type

class Extension(BaseExtension):
    namespace = NAMESPACE
    update_interval = 0.5

    def init(self, config):
        """ Setup the readers for nfc """
        self.config = config
        self.readers = {}
        self.tags = self.mudpi.cache.setdefault(NAMESPACE, {}).setdefault('tags', {})

        if not isinstance(config, list):
            config = [config]

        for conf in config:
            key = conf.get('key')
            if key not in self.readers:
                self.readers[key] = NFCReader(self.mudpi, conf)

        return True

    def validate(self, config):
        """ Validate the nfc configs """
        config = config[self.namespace]
        if not isinstance(config, list):
            config = [config]

        for conf in config:
            key = conf.get('key')
            if key is None:
                raise ConfigError('NFC missing a `key` in config')

            model = conf.get('model')

            address = conf.get('address')
            if address is None:
                if model is None:
                    raise ConfigError('NFC missing an `address` in config')
                else:
                    if model in NFCReader.models:
                        conf['address'] = NFCReader.models[model]
                    else:
                        raise ConfigError('NFC missing an `address` in config and a default could not be set.')

        return config


class NFCReader(Worker):

    # Default addresses for common models
    models = {
    'RC-S330': 'usb:054c:02e1',
    'RC-S360': 'usb:054c:02e1',
    'RC-S370': 'usb:054c:02e1',
    'RC-S380/S': 'usb:054c:06c1',
    'RC-S380/P': 'usb:054c:06c3',
    'PN531v4.2': 'usb:054c:0193',
    'SCL3710': 'usb:04cc:0531',
    'ACR122U': 'usb:072f:2200',
    'Stollmann': 'tty:USB0:pn532',
    'SCL3711': 'usb:04e6:5591',
    'SCL3712': 'usb:04e6:5593',
    'StickID': 'usb:04cc:2533',
    'ADRA': 'tty:USB0:arygon'
    }

    """ Worker to manage a NFC reader connection """
    def __init__(self, mudpi, config):
        self.mudpi = mudpi
        self.config = config
        self._tags = self.mudpi.cache.setdefault(NAMESPACE, {}).setdefault('tags', {})
        self._tags.update(self.tags)
        self._uids = self.mudpi.cache.setdefault(NAMESPACE, {}).setdefault('uids', {})
        self._logs = self.mudpi.cache.setdefault(NAMESPACE, {}).setdefault('logs', [])
        self.last_tag = {}
        self.last_uid = None

        self._thread = None
        self._lock = threading.Lock()
        self._ready = threading.Event()
        self.reset_duration()
        self.mudpi.workers.register(self.key, self)

    @property
    def key(self):
        """ Unique key for the reader """
        return self.config.get('key').lower()
    
    @property
    def ready(self):
        """ Return if nfc is initialized """
        return self._ready.is_set()

    @property
    def read_delay(self):
        """ Delay inbetween readings to reset the reader """
        return self.config.get('read_delay', 0.5)

    @property
    def address(self):
        """ Address for the reader device """
        return self.config.get('address', 'usb:072f:2200')

    @property
    def tracking(self):
        """ Enables scan tracking and writes scan count to the tag """
        return self.config.get('tracking', False)

    @property
    def writing(self):
        """ Enables writing to the tag"""
        return self.config.get('writing', False)

    @property
    def beep_enabled(self):
        """ Enables beeper when tag is scanned (If supported) """
        return self.config.get('beep_enabled', False)

    @property
    def persist_records(self):
        """ Enables records to be appended to instead of overwritten """
        return self.config.get('persist_records', True)

    @property
    def tags(self):
        """ Preregistered tags for the reader. 
            If save_tags is true this will 
            update as tags get scanned in.  """
        return self.config.get('tags', {})

    @property
    def save_tags(self):
        """ Enable scanned tags being saved to config """
        return self.config.get('save_tags', False)

    @property
    def default_records(self):
        """ Get default records to write to tags """
        return self.config.get('default_records')

    @property
    def store_logs(self):
        """ Enable tag log list of recent scans """
        return self.config.get('store_logs', False)

    @property
    def log_length(self):
        """ Max length of logs to store """
        return self.config.get('log_length', 100)
    

    """ Methods """
    def work(self, func=None):
        """ Main NFC read cycle """
        while self.mudpi.is_prepared:
            if self.mudpi.is_running:
                try:
                    with nfc.ContactlessFrontend(self.address) as clf:
                        while self.mudpi.is_running:
                            try:
                                tag = clf.connect(rdwr={'on-connect': self.handle_read, 'beep-on-connect': self.beep_enabled, 'on-release': self.handle_release}, terminate=self.terminate)
                                time.sleep(self.read_delay)
                            except Exception as error:
                                Logger.log(LOG_LEVEL["error"],
                                    f"Worker {self.key} NFC Scan Error: {error}")
                                time.sleep(2)

                except Exception as error:
                    Logger.log_formatted(LOG_LEVEL["error"],
                        f"Worker {self.key} NFC Reader Error: {error}")
                    time.sleep(2)

        # MudPi Shutting Down, Perform Cleanup Below
        Logger.log_formatted(LOG_LEVEL["debug"],
                   f"Worker {self.key} ", "Stopping", "notice")
        Logger.log_formatted(LOG_LEVEL["info"],
                   f"Worker {self.key} ", "Offline", "error")

    def handle_read(self, tag):
        """ Handle a tag being scanned by the reader """
        count = None
        tag_uid = None
        records = []

        if not tag:
            time.sleep(0.1)
            Logger.log(LOG_LEVEL["error"],
                f"Worker {self.key} NFC Tag Read Error")
            return

        tag_serial = tag.identifier.hex()
        self.last_tag = tag
        _tag_data = self.parse_tag(tag)
        tag_uid = _tag_data.get('tag_uid')

        self.fire(_tag_data)

        if tag_serial not in self._tags:
            Logger.log(LOG_LEVEL["info"],
                f"New NFC Tag Scanned: {FONT_CYAN}{tag_serial}{FONT_RESET}")
            self._tags[tag_serial] = _tag_data
            event_data = {'event': 'NFCNewTagScanned'}
            event_data.update(_tag_data)
            self.fire(event_data)
            if self.save_tags:
                self.config.setdefault('tags', {})[tag_serial] = _tag_data
                self.mudpi.save_config()
        else:
            Logger.log(LOG_LEVEL["info"],
                f"Existing NFC Tag Scanned: {FONT_CYAN}{tag_serial}{FONT_RESET}")

            # Check if UID is registered
            if self._tags[tag_serial].get('tag_uid'):
                if tag_uid:
                    if tag_uid != self._tags[tag_serial]['tag_uid']:
                        event_data = {'event': 'NFCTagUIDMismatch', "existing_tag_uid": self._tags[tag_serial]['tag_uid']}
                        event_data.update(_tag_data)
                        self.fire(event_data)
                        Logger.log(LOG_LEVEL["debug"],
                            f"WARNING: Tag Data UID Mismatch for tag: {FONT_CYAN}{tag_serial}{FONT_RESET}")
                else:
                    event_data = {'event': 'NFCTagUIDMissing', "existing_tag_uid": self._tags[tag_serial]['tag_uid']}
                    event_data.update(_tag_data)
                    self.fire(event_data)
                    Logger.log(LOG_LEVEL["debug"],
                        f"Notice: Tag UID registered but Missing on tag: {FONT_CYAN}{tag_serial}{FONT_RESET}")

        # Register the UID and check for duplicates
        if tag_uid:
            if tag_uid not in self._uids:
                self._uids[tag_uid] = {'tags': [tag_serial]}
            else:
                _prev_tags = self._uids[tag_uid].setdefault('tags', [])
                if tag_serial not in _prev_tags:
                    self._uids[tag_uid]['tags'].append(tag_serial)
                    if len(_prev_tags) > 2:
                        event_data = {'event': 'NFCDuplicateUID', "existing_tag_id": self._tags[tag_serial]['tag_uid']}
                        event_data.update(_tag_data)
                        self.fire(event_data)
                        Logger.log(LOG_LEVEL["debug"],
                            f"WARNING: Same Tag UID found in multiple tags: {FONT_CYAN}{_prev_tags}{FONT_RESET}")

        # Handle the ndef records and tracking info
        if not tag.ndef:
            if self.tracking:
                self.write(tag, self.add_default_records())       
        else:
            if tag.ndef.records:
                for record in tag.ndef.records:
                    if record.type == TYPE_TEXT:
                        if self.persist_records:
                            if not record.text.startswith('count:'):
                                records.append(record)
                    elif record.type == TYPE_URI:
                        if self.persist_records:
                            records.append(record)
                    else:
                        if self.persist_records:
                            records.append(record)

            if self.tracking:
                if _tag_data.get('count') is None:
                    count = 0
                    records.append(ndef.TextRecord(f"count:{count}"))
                else:
                    count = _tag_data['count'] + 1
                    records.append(ndef.TextRecord(f"count:{count}"))

            if self.tracking:
                _defaults = self.add_default_records(records, tag_serial)
                self.write(tag, _defaults)

        # Create a UUID if one was not set
        if tag_uid is None:
            if self.writing:
                Logger.log(LOG_LEVEL["debug"],
                    f"No Tag UID Found for Tag: {FONT_CYAN}{tag_serial}{FONT_RESET}. A new one was generated and saved.")
                _tag_data = self.parse_tag(tag)
                _tag_data['tag_uid'] = self.last_uid
                self._tags[tag_serial] = _tag_data
                event_data = {'event': 'NFCNewUIDCreated'}
                event_data.update(_tag_data)
                self.fire(event_data)
                if self.save_tags:
                    self.config.setdefault('tags', {})[tag_serial].update(self._tags[tag_serial])
                    self.mudpi.save_config()
            else:
                Logger.log(LOG_LEVEL["debug"],
                    f"No Tag UID Found for Tag: {FONT_CYAN}{tag_serial}{FONT_RESET}. A new one can not be saved because `writing` is disabled.")

        if self.store_logs:
            _tag_log = {'tag_id': tag_serial, 
                'tag_uid': tag_uid, 
                'count': count,
                'updated_at': str(datetime.datetime.now().replace(microsecond=0)) }
            self._logs.append(_tag_log)
            if len(self._logs) > self.log_length:
                self._logs.pop(0)
            self.store_current_logs()
        return True

    def write(self, tag, records=[]):
        """ Write data to a NFC card """
        if self.writing:
            tag.ndef.records = records
        return True

    def add_default_records(self, records=[], tag_id=None):
        """ Return default records to write to a tag """
        _default_records = None
        if tag_id:
            if tag_id in self.tags:
                if self.tags[tag_id].get('default_records'):
                    _default_records = self.tags[tag_id]['default_records']
        
        if _default_records is None and self.default_records is not None:
            _default_records = self.default_records

        if _default_records is None:
            _txt_mudpi = ndef.TextRecord("MudPi")
            if _txt_mudpi not in records:
                records.insert(0, _txt_mudpi)

            _uri_mudpi = ndef.UriRecord("https://mudpi.app/docs/extension-nfc")
            if _uri_mudpi not in records:
                records.insert(1, _uri_mudpi)

            _txt_count_label = ndef.TextRecord("Matthew 15:13")
            if _txt_count_label not in records:
                records.insert(2, _txt_count_label)
        else:
            if isinstance(_default_records, list):
                for default_record in _default_records:
                    _record = None
                    if default_record.get('type', '').lower() == 'text':
                        if default_record.get('data'):
                            _record = ndef.TextRecord(default_record['data'])
                    elif default_record.get('type', '').lower() == 'uri':
                        if default_record.get('data'):
                            _record = ndef.UriRecord(default_record['data'])

                    if _record:
                        if _record not in records:
                            if default_record.get('position') is not None:
                                try:
                                    _position = int(default_record['position'])
                                    records.insert(_position, _record)
                                except Exception:
                                    records.append(_record)
                            else:
                                records.append(_record)

        _has_count = False
        _has_uid = False
        _to_remove = []
        for r in records:
            if r.type == TYPE_TEXT:
                if r.text.startswith('count:'):
                    if not _has_count:
                        _has_count = True
                    else:
                        # count already found, remove duplicate
                        _to_remove.append(r)
                elif r.text.startswith('uid:'):
                    if not _has_uid:
                        _has_uid = True
                    else:
                        # uid already found, remove duplicate
                        _to_remove.append(r)
                elif r.text.startswith('last_scan:'):
                    if self.tracking:
                        # remove it to replace with updated data
                        _to_remove.append(r)

        if _to_remove:
            for record in _to_remove:
                records.remove(record)

        if not _has_uid:
            self.last_uid = uid = str(uuid4())
            records.append(ndef.TextRecord(f"uid:{uid}"))

        if self.tracking:
            if not _has_count:
                records.append(ndef.TextRecord("count:0"))

            records.append(ndef.TextRecord(f"last_scan:{datetime.datetime.now().replace(microsecond=0).strftime('%Y-%m-%d %H:%M:%S')}"))
    
        return records

    def terminate(self):
        """ Function to close out a blocking read call """
        return not self.mudpi.is_running

    def handle_release(self, tag):
        """ Handle the tag remove event """
        _tag_data = self.parse_tag(tag)
        event_data = {'event': 'NFCTagRemoved'}
        event_data.update(_tag_data)
        self.fire(event_data)

    def fire(self, data={}):
        """ Fire a control event """
        _event_data = {
            'event': 'NFCTagScanned',
            'data': {
                'reader_id': self.key,
                'key': self.key,
                'updated_at': str(datetime.datetime.now().replace(microsecond=0))
        }}
        _event_data['data'].update(data)
        self.mudpi.events.publish(NAMESPACE, _event_data)
        return True

    def parse_tag(self, tag):
        """ Parse a tag into a dict """
        _data = {
            'tag_id': tag.identifier.hex()
        }
        _ndef_data = []
        _ndef_records = []

        if not tag.ndef:
            return _data

        _data['capacity'] = tag.ndef.capacity
        _data['used_capacity'] = tag.ndef.length
        _data['writeable'] = tag.ndef.is_writeable
        _data['readable'] = tag.ndef.is_readable

        if not tag.ndef.records:
            return _data

        for record in tag.ndef.records:
            if record.type == TYPE_TEXT:
                if record.text:
                    if record.text.startswith('count:'):
                        try:
                            
                            _data['count'] = int(record.text.split('count:', 1)[1])
                        except Exception:
                            _data['count'] = 0
                    elif record.text.startswith('uid:'):
                        _data['tag_uid'] = record.text.split('uid:', 1)[1]
                    else:
                        _ndef_data.append(record.text)
            elif record.type == TYPE_URI:
                if record.uri:
                    _ndef_data.append(record.uri)
            else:
                if record.data:
                    _ndef_data.append(record.data)
            _ndef_records.append(record)
        if _ndef_data:
            _data['ndef'] = _ndef_data
        return _data

    def store_current_logs(self):
        """ Stores the current logs into the MudPi state manager """
        if not self.store_logs:
            return

        if self.mudpi is None:
            raise MudPiError("MudPi Core instance was not provided!")

        data = self.mudpi.states.set(self.key, self._logs.copy(), self.config)
        return data