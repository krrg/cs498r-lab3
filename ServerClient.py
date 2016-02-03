import errno
import socket


class KeyValueStore(object):

    def __init__(self):
        self.values = {}

    def get(self, key):
        return self.values.get(key, None)

    def delete(self, key):
        self.values.pop(key, None)

    def set(self, key, value):
        self.values[key] = value

globalStore = KeyValueStore()


class ServerClient(object):

    def __init__(self, socket):
        self.socket = socket
        self.data = ""

    def close(self):
        self.socket.close()

    def parse_command(self):
        chunks = self.data.strip().split()

        if chunks[0] == 'GET':
            self.handle_GET(chunks)
        elif chunks[0] == 'SET':
            self.handle_SET(chunks)
        elif chunks[0] == 'DEL':
            self.handle_DEL(chunks)
        else:
            self.handle_INVALID()

        self.data = ""

    def handle_GET(self, chunks):
        if len(chunks) != 2:
            return self.handle_BAD_LENGTH(chunks)
        value = str(globalStore.get(chunks[1]))
        self.send("{}\n".format(value))

    def handle_SET(self, chunks):
        if len(chunks) != 3:
            return self.handle_BAD_LENGTH(chunks)
        globalStore.set(chunks[1], chunks[2])
        self.send("1\n")

    def handle_DEL(self, chunks):
        if len(chunks) != 2:
            return self.handle_BAD_LENGTH(chunks)
        result = 0 if globalStore.get(chunks[1]) is None else 1
        globalStore.delete(chunks[1])
        self.send("{}\n".format(result))

    def handle_INVALID(self, chunks):
        self.send("Invalid command `{}`\n".format(chunks[0]))

    def handle_BAD_LENGTH(self, chunks):
        self.send("Wrong number of parameters ({}) for command `{}`\n".format(len(chunks), chunks[0]))

    def send(self, out_bytes):
        remaining = 0
        while remaining < len(out_bytes):
            try:
                sent_result = self.socket.send(out_bytes[remaining:])
                if sent_result == errno.EWOULDBLOCK or sent_result <= 0:
                    continue
                remaining += sent_result
            except socket.error, (value, message):
                if value == errno.EWOULDBLOCK:
                    continue
                else:
                    return
            except Exception as e:
                print str(e)
                return

    def read_all_available(self):
        try:
            while True:
                # Keep reading chunks until exception is thrown.
                print "Reading chunk on {}".format(self.socket.fileno())
                chunk = self.socket.recv(256)
                print "Done reading chunk on {}".format(self.socket.fileno())
                self.handle_data_available(chunk)
        except socket.error, (errtype, msg):
            if errtype == errno.EAGAIN or errno.EWOULDBLOCK:
                return
            else:
                print ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>> There was a big old error."
                print format_exc()


    def handle_data_available(self, data):
        for c in data:
            if c == '\n':
                self.parse_command()
            elif c == '\0':
                self.close()
                return
            elif c == '\r':
                continue  # Skip carriage returns.
            else:
                self.data += c
