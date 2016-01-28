__author__ = 'krr428'

from sys import exit
from traceback import format_exc


import socket
import errno


class HttpClientsManager(object):

    def __init__(self, http_handlers, func_unregister=lambda: None):
        self.asockets = {}  # Active sockets
        self.arequests = {}  # Active requests
        self.http_handlers = http_handlers
        self.func_unregister = func_unregister

    def get_older_than(self, seconds):
        stale_sockets = []
        for socket_index in self.arequests:
            if self.arequests[socket_index].get_seconds_idle() > seconds:
                stale_sockets.append(socket_index)
        return stale_sockets

    def remove_older_than(self, seconds):
        map(self.__mark_for_deletion, self.get_older_than(seconds))

    def __mark_for_deletion(self, file_desc):
        self.func_unregister(file_desc)
        if file_desc not in self.asockets:
            return
        self.asockets[file_desc].close()
        del self.asockets[file_desc]
        del self.arequests[file_desc]

    def __getitem__(self, index):
        return {
            'socket': self.asockets[index],
            'request': self.arequests[index]
        }

    def __setitem__(self, file_desc, socket_obj):
        self.asockets[file_desc] = socket_obj
        self.arequests[file_desc] = HttpRequest()

    def __contains__(self, item):
        return item in self.asockets and item in self.arequests

    def read_from_client(self, file_desc, max_chunk_size=1024):
        try:
            while True:
                # Keep reading chunks off until
                chunk = self.asockets[file_desc].recv(max_chunk_size)
                if self.__offer_chunk_to(file_desc, chunk):
                    break
        except socket.error, (errtype, message):
            if errtype == errno.EAGAIN or errno.EWOULDBLOCK:
                return
            else:
                print format_exc()
                exit(1)

    def __offer_chunk_to(self, file_desc, chunk):
        was_entire_message_received = False

        if not chunk:
            self.__mark_for_deletion(file_desc)
            return True  # True meaning, this client is done.

        self.arequests[file_desc].offer(chunk)
        while self.arequests[file_desc].finished:
            was_entire_message_received = True

            self.__handle_request(self.arequests[file_desc])

            self.__send_raw_binary(file_desc, resp_head)
            self.__send_raw_binary(file_desc, resp_body)

            overflow = self.arequests[file_desc].excess
            self.arequests[file_desc] = HttpRequest()
            self.arequests[file_desc].offer(overflow)

        return was_entire_message_received

    def __send_raw_binary(self, file_desc, out_bytes):
        remaining = 0
        while remaining < len(out_bytes):
            try:
                sent_result = self.asockets[file_desc].send(out_bytes[remaining:])
                if sent_result == errno.EWOULDBLOCK or sent_result <= 0:
                    continue
                remaining += sent_result
            except socket.error, (value, message):
                if value == errno.EWOULDBLOCK:
                    continue

    def __handle_request(self, request):
        print request.request
