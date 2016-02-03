import select
import socket
import sys
import errno
from ServerClient import ServerClient

class Server(object):

    def __init__(self, port, timeout=15):
        self.port = port
        self.server = None
        self.poller = None
        self.pollmask = select.EPOLLIN | select.EPOLLHUP | select.EPOLLERR
        self.idle_timeout = timeout
        self.clientList = {}

    def start_server(self):
        self.server = self.__create_server_socket()
        self.poller = select.epoll()  # Use epoll as polling mechanism instead of raw select().
        self.poller.register(self.server, self.pollmask)   # Tell epoll we want to listen to our server socket for IO events.
        print "Server has started on port ", self.port
        self.__event_loop()

    def __event_loop(self):
        """ This is the core reactor part"""
        while True:
            try:
                self.__event_loop_single(self.poller.poll(timeout=1))
            except Exception as e:
                print e
                print str(e)
                print "Continuing event loop..."

    def __event_loop_single(self, ready):
        """A single iteration of the event loop"""

        # Loop through any available clients
        for socketnum, event in ready:
            if event & (select.POLLHUP | select.POLLERR):
                self.__handle_error(socketnum)
            elif socketnum == self.server.fileno():
                # If it is the server socket, then we need to `accept()`
                self.__handle_new_clients()
            else:
                # If it is a client sending us data, then go handle them too.
                self.__handle_existing_client(socketnum)

    def __handle_existing_client(self, fd):
        if fd in self.clientList:
            self.clientList[fd].read_all_available()

    def __handle_new_clients(self):
        try:
            while True:
                client, addr = self.server.accept()  # Accept the client
                print "Accepting new client {}, {}".format(client.fileno(), addr)
                client.setblocking(0)     # Make certain that the client will not block
                self.clientList[client.fileno()] = ServerClient(client)
                self.poller.register(client.fileno(), self.pollmask)  # Begin listening to the client.
        except socket.error, (value, message):
            if value == errno.EAGAIN or errno.EWOULDBLOCK:
                return  # suppress if we would block or if we just need to try again

    def __handle_error(self, client):
        self.poller.unregister(client)  # If you cause errors, we just disconnect you.
        if client == self.server.fileno():   # Unless you were the server socket...
            self.server.close()
            self.server = self.__create_server_socket()
            self.poller.register(self.server, self.pollmask)  # ...in which case we reconnect.
        else:
            del self.clientList[client.fileno()]


    def __create_server_socket(self):
        server = None
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(("", self.port))
            server.listen(5)  # backlog=5
            server.setblocking(0)
            return server
        except socket.error, (value, message):
            if server:
                server.close()
            print "Could not open socket: " + message
            sys.exit(1)
