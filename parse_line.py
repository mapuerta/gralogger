import re

class ParseLogLine():
    def __init__(self, formatter, delimiter=None, format_colms=None):
        self.delimiter = delimiter
        self.format_colms = format_colms
        self.formatter = formatter

    def split_colunms(self, line):
        pass

    def re_compile(self, line):
        pattern = re.compile(self.formatter)
        matches = pattern.match(line)
        try:
            groupdict = matches.groupdict()
        except Exception as error:
            print "[warning]: pattern not match: ",line
            return False
        return groupdict

    def parse_line(self, line):
        if self.delimiter:
            line = self.split_colunms(line)
        data = self.re_compile(line)
        return data
