import socket
import time

HOST = "echo-server"  # The server's hostname or IP address
PORT = 65432  # The port used by the server

if __name__ == '__main__':
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))

        while True:
            time.sleep(0.01)
            stime = time.time()
            s.sendall(b"x" * 64)
            data = s.recv(1024)
            ftime = time.time()
            delay = ftime - stime
            print(f"Measured {delay:.8f} secs delay")
