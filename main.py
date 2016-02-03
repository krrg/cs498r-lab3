__author__ = 'krr428'

from Server import Server
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='Echo Server', description='An HTTP Server, supporting GET and HEAD requests.', add_help=True)
    parser.add_argument('-p', '--port', type=int, action='store', help='port the server will bind to',default=8080)
    parser.add_argument('-d', '--debug', action='store_true', help='whether or not to display debugging info')
    args = parser.parse_args()

    # I have no debugging info to output.
    if args.debug:
        print "Starting server on port: ", args.port

    try:
        Server(args.port).start_server()
    except Exception as e:
        print e
        print "The server experienced an error and will now shutdown."
