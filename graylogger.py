import pygelf
import logging
import re
import multiprocessing
import time, os
import json
from parse_line import ParseLogLine


class Collector(multiprocessing.Process):
    def __init__(self, host, port, protocol, source, path, formatter, flush_interval, kwargs):
        multiprocessing.Process.__init__(self)
        self.host = host
        self.port = int(port)
        self.proto = protocol
        self.source = source
        self.queue = []
        self.formatter = formatter
        self.path_log = path
        self.timestart = time.time()
        self.flush_interval = flush_interval
        self.kwargs = kwargs
        self.create_socket()

    @property
    def restart(self):
        self.timestart = time.time()

    @property
    def flush(self):
        interval = {'s': lambda x: x*1,
                    'm': lambda x: x*60,
                    'h': lambda x: x*3600}
        flush = re.match(r"(?P<interval>[0-9]+)(?P<unit>s|m|h)+",
                         self.flush_interval)
        if flush:
            flush = interval[flush.group('unit')](float(flush.group('interval')))
        else:
            flush = float(self.flush_interval)
        return flush

    def alarm(self):
        if (time.time() - self.timestart) >= self.flush:
            self.send_log()
            self.clear_queue()
            self.restart

    def create_socket(self):
        paramsproto = {'tcp': {},
                       'udp': {'chunk_size': 1300},
                       'tls': {'validate': False, 'ca_certs': None,
                               'certfile': None, 'keyfile': None},
                       'http': {'path': '/gelf', 'timeout': 5}}
        for key, value in self.kwargs.items():
            if key in paramsproto[self.proto]:
                paramsproto[self.proto][key] = value
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)
        handler_str = "Gelf{}Handler".format(self.proto.capitalize())  
        func = getattr(pygelf, handler_str)
        self.logger.addHandler(func(self.host, self.port, include_extra_fields=True,
                                    **paramsproto[self.proto]))

    def check_message(self, data):
        loglevels = {'DEBUG': logging.DEBUG,
                     'INFO': logging.INFO,
                     'WARNING': logging.WARNING,
                     'ERROR': logging.ERROR,
                     'CRITICAL': logging.CRITICAL}
        standard_msg = {"facility": "PythonLogger",
                        "version": "1.0",
                        "level": 1,
                        "message": None,
                        "source": self.source}
        for key, value in standard_msg.items():
            if key not in data:
                data[key] = value
        for key, value in standard_msg.items():
            if key == 'level':
                if data[key] in loglevels:
                    data[key] = loglevels[data[key].upper()]
                else:
                    data[key] = logging.DEBUG
        return data

    def send_log(self):
        try:
            for data in self.queue:
                data = self.check_message(data)
                message = data['message']
                level =  data['level']
                source =  data['source']
                data.pop('message')
                data.pop('level')
                self.logger.log(level, message, extra=data)
                print "sending: {source} {level} {message} {data}".\
                    format(source=self.source, message=message,
                           data=data, level=logging.getLevelName(level))
        except Exception as e:
            print "Exception during log operation: {0}".format(e)

    def parse_data(self, line):
        parselog = ParseLogLine(self.formatter, **self.kwargs)
        return parselog.parse_line(line)

    def run(self):
        filename = self.path_log
        file = open(filename,'r')
        st_results = os.stat(filename)
        st_size = st_results[6]
        file.seek(st_size)
        while True:
            self.alarm()
            where = file.tell()
            line = file.readline()
            if not line:
                time.sleep(1)
                file.seek(where)
            else:
                data = self.parse_data(line)
                if data:
                    self.queue.append(data)

    def clear_queue(self):
        self.queue = []

    def exit(self):
        self.signal_exit()
        while self.is_alive():
            time.sleep(1)
