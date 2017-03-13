#!/usr/bin/env python
import argparse
import socket
import sys
import time


def wait_net_service(server, port, timeout=None):
    """
    Wait for network service to appear
    @param timeout: in seconds, if None or 0 wait forever
    @return: True of False, if timeout is None may return only True or
             throw unhandled network exception

    Adapted from https://code.activestate.com/recipes/576655/ (MIT)
    """
    address = (server, port)
    if timeout:
        end = time.monotonic() + timeout

    while True:
        s = socket.socket()
        if timeout:
            next_timeout = end - time.monotonic()
            if next_timeout < 0:
                raise RuntimeError('timed out')
            else:
                s.settimeout(next_timeout)
        try:
            s.connect(address)

        except socket.timeout as e:
            if timeout:
                raise RuntimeError('timed out')

        except ConnectionRefusedError as e:
            time.sleep(0.1)

        else:
            s.close()
            return True


def main(argv=None):
    if argv is None:
        argv = sys.argv

    parser = argparse.ArgumentParser(description='Wait for a service to come up')
    parser.add_argument('-H', '--host', type=str, help="Host name", default='127.0.0.1')
    parser.add_argument('-p', '--port', type=int, help="Port", default=8000)
    parser.add_argument('-t', '--timeout', type=float, help="Timeout", default=10)
    args = parser.parse_args(argv[1:])

    if args.timeout <= 0:
        timeout = None
    else:
        timeout = args.timeout

    try:
        wait_net_service(args.host, args.port, timeout)
    except RuntimeError as e:
        if 'timed' not in str(e):
            raise
        print('timed out waiting for {}:{}'.format(args.host, args.port),
              file=sys.stderr)
        return -1

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
