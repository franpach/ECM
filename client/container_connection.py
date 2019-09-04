# connection with container

import socket
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--port", help="Port to connect to", type=int)
parser.add_argument("-w", "--id", help="Client ID")
args = parser.parse_args()

BUFFER_SIZE = 1024
TCP_IP = "127.0.0.1"

error = 0
if not args.id:
        error = 1
        print("ERROR. Has de proveer obligatoriamente una identificacion de cliente")
else:
        id = args.id

if not args.port:
        error = 1
        print("ERROR. Has de proveer obligatoriamente un puerto al que conectarte")
else:
        port = args.port

if error == 0:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((TCP_IP, port))
        try:
                message = id.encode()
                s.send(message)
                while True:
                        resp=s.recv(BUFFER_SIZE)
                        if not resp: break
                        print(resp.decode())
        except KeyboardInterrupt:
                print('Interrupted!')
                s.close()
        except Exception as e:
                print(e)
                print("Conexion cerrada inesperadamente")
                s.close()
