import argparse
import ConfigParser
import os
from graylogger import Collector


class Parsecfg():
    def __init__(self, filename):
        self.config = ConfigParser.ConfigParser()
        self.config.read(filename)

    def load(self):
        return self.config

def find_file_conf():
    filename = "graylogger.conf"
    fileconf = None
    for fileconf in os.listdir('.'):
        if fileconf == filename:
            return fileconf
    for fileconf in os.listdir('/etc'):
        if fileconf == filename:
            return fileconf
    return fileconf


def check_args():
    options_args = {"host": None, "port": 12201,
                    "protocol": 'udp', "source": None,
                    "formatter": None, "path": None,
                    "flush_interval": None,
                    }
    return options_args


parser = argparse.ArgumentParser(description='send a message to a graylog server',
    usage='%(prog)s -c graylog-agent.conf')
parser.add_argument("-c", "--config", help="Indicate graylog-agent.conf")
args = parser.parse_args()

def main():
    pass_args = check_args()
    if not args.config:
       args.config = find_file_conf()
    filename = args.config
    parsecfg = Parsecfg(filename).load()
    for section in parsecfg.sections():
        kwargs = {"delimiter": None, "format_colms": None,}
        items =  parsecfg.items(section)
        for key, value in items:
            if key in pass_args:
                pass_args[key] = value
            else:
                kwargs[key] = value
        pass_args.update({'source': section})
        pass_args.update({'kwargs': kwargs})
        graylog = Collector(**pass_args)
        graylog.start()
    print "Runnig service"


if __name__ == '__main__':
    main()

