# client registration

import socket
import argparse
import json

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--company", help="Company name", default="null")
args=parser.parse_args()

ERROR = 0
BUFFER_SIZE = 1024
TCP_IP = "127.0.0.1"
PORT = 10000
COMPANY = args.company

if COMPANY == "null":
        print("ERROR. Hay que proporcionar el nombre de compania")
        ERROR=1

if ERROR == 0:
        json_message = {
                "company":COMPANY
        }
        message = json.dumps(json_message)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((TCP_IP, PORT))
        sock.send(message.encode())
        resp = sock.recv(BUFFER_SIZE)
        sock.close()

        print("Respuesta recibida: {}".format(resp))
