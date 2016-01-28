__author__ = 'krr428'

from collections import deque
from datetime import datetime
from abc import ABCMeta, abstractmethod


class HttpRequest(object):

    def __init__(self):
        self.cache = []
        self.timestamp = datetime.now()
        self.request = None
        self.headers = {}
        self.finished = False
        self.parse_error = False
        self.excess = []

    def offer(self, incoming):
        self.timestamp = datetime.now()
        if self.__contains_newline(incoming):
            self.cache.extend(incoming)
            try:
                self.__parse_cache()
            except Exception:
                self.parse_error = True
                self.finished = True
                return
        else:
            self.cache.extend(incoming)

    def __contains_newline(self, incoming):
        lookback = min(3, len(self.cache))
        chunk = "".join(self.cache[-lookback:]) + "".join(incoming)
        return chunk.find("\n") >= 0

    def __parse_cache(self):
        requests = "".join(self.cache).split("\n", 1)
        request = requests[0]
        if len(requests) > 1:
            self.excess.extend(requests[1])
        self.__parse_request(request)

    def __parse_request(self, request):
        request_line = request.strip()

        arguments = request_line.split()
        if arguments[0] not in ['GET', 'DEL', 'SET']:
            __parse_error()

        # TODO: Add error for wrong number of arguments.

        self.request = arguments
        self.finished = True
        return

    def __parse_error(self):
        self.parse_error = True
        self.finished = True
        raise RedisParseError()

    def get_seconds_idle(self):
        return (datetime.now() - self.timestamp).total_seconds()


class RedisParseError(BaseException):
    pass
