__author__ = 'krr428'

from Server import HttpServer
from WebConf import WebConf
import argparse

def create_req_handlers(filename='web.conf'):
    wconf = WebConf.read_global_configuration(filename)
    request_handlers = {}
    for host in wconf.hosts:
        request_handlers[host] = HttpRequestHandler(wconf.hosts[host], mime_types=wconf.mimetypes)
    return request_handlers, wconf

if __name__ == "__main__":
    req_handlers, wc = create_req_handlers()

    parser = argparse.ArgumentParser(prog='Echo Server', description='An HTTP Server, supporting GET and HEAD requests.', add_help=True)
    parser.add_argument('-p', '--port', type=int, action='store', help='port the server will bind to',default=8080)
    parser.add_argument('-d', '--debug', action='store_true', help='whether or not to display debugging info')
    args = parser.parse_args()

    # I have no debugging info to output.
    if args.debug:
        print "Starting server on port: ", args.port

    try:
        HttpServer(args.port, req_handlers, int(wc.params['timeout']) if 'timeout' in wc.params else 15).start_server()
    except:
        print "The server experienced an error and will now shutdown."
