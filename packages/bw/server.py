#!/usr/bin/python3

from socket import *

BUFSIZE = 32
port = 5678


def server():
    s = socket(AF_INET, SOCK_STREAM)
    s.bind(('', port))
    s.listen(1)
    print('Server ready...')

    try:
        while True:
            conn, (host, remoteport) = s.accept()
            try:
                print(f'Connected to {host}:{remoteport}')
                while True:
                    conn.recv(BUFSIZE)
            except ConnectionResetError:
                print(f'Done with {host}:{remoteport}')
    except KeyboardInterrupt:
        print("Exiting...")
    s.shutdown(1)


if __name__ == '__main__':
    server()
