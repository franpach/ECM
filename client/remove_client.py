# client removal

import socket
import argparse
import json

#Comprueba que el identificador privado que provee el cliente es valido
def check_client(who):
        return True

parser = argparse.ArgumentParser()
parser.add_argument("-w", "--who", help="Private identification of the client", default="null")
parser.add_argument("-i", "--id", help="ID of the service to be removed", default="null")
args = parser.parse_args()

ERROR = 0
BUFFER_SIZE = 1024
TCP_IP = "127.0.0.1"
PORT = 10002
ID = args.id
WHO = args.who

if not check_client(WHO):
        print("ERROR. Identificador privado no valido")
        ERROR = 1

if ID == "null":
        print("ERROR. Hay que proporcionar un ID de servicio")
        ERROR = 1

if ERROR == 0:
        json_message = {
                "who":WHO,
                "id":ID,
        }
        message = json.dumps(json_message)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((TCP_IP, PORT))
        sock.send(message)
        resp = sock.sock.recv(BUFFER_SIZE)
        sock.close()

        print("Respuesta recibida: {}").format(resp)
