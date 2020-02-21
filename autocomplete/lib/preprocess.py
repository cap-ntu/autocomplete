import json
from abc import abstractmethod

from autocomplete.lib.constants import ENCODING
from autocomplete.lib.log import tqdm_lim


def write_json(file, raw_json):
    with open(file, mode='w', encoding=ENCODING) as f:
        f.write(json.dumps(raw_json))


def read_lines(file, total=None, lim=None):
    with open(file, mode='r', encoding=ENCODING) as f:
        for line in tqdm_lim(f, total=total, lim=lim):
            yield line


def read_jsons(*files, lim=None):
    for file in files:
        for line in read_lines(file, lim=lim):
            yield json.loads(line)


def read_json(file):
    return list(read_jsons(file))[0]


class JsonExtractor:

    @abstractmethod
    def extract(self, raw_json):
        pass


class JsonListKeyExtractor(JsonExtractor):
    def __init__(self, key):
        self.key = key

    def extract(self, raw_json):
        for node in raw_json:
            if node == 0:
                break

            if self.key in node:
                yield node[self.key]


def extract_jsons_info(extractor: JsonExtractor, *files, lim=None):
    for raw_json in read_jsons(*files, lim=lim):
        yield extractor.extract(raw_json)

