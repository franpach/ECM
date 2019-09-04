# random data generator
# generates a tuple of values {temperature, humidity} 

import random
import socket
import argparse
import time
import json

# Crea el mensaje enviado al servidor
# Returns: El json enviado
def create_message(id, temp, hum):
        json_message = {
                "id":id,
                "temp":temp,
                "hum":hum
        }
        return json_message

parser = argparse.ArgumentParser()
parser.add_argument("-w", "--id", help="Client ID", default="null")
parser.add_argument("-n", "--nbatch", help="Number of values to send", default=500, type=int)
parser.add_argument("-f", "--frequence", help="Time between each data", default=1, type=int)
args=parser.parse_args()

IP = "127.0.0.1"
BOOTSTRAP_PORT = 3000
BUFFER_SIZE = 1024
ID = args.id
NBATCH = args.nbatch
FREQUENCE = args.frequence
ERROR = 0

if ID == "null":
        print("ERROR. Debes proporcionar un identificador de cliente")
        ERROR = 1
        
if FREQUENCE < 0.5:
        print("WARNING. La frecuencia no puede ser tan baja. Asignando por defecto (1)...")
        FREQUENCE = 1

if ERROR == 0:

        sockb = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sockb.connect((IP, BOOTSTRAP_PORT))

        message = ID.encode()
        sockb.send(message)
        resp = sockb.recv(BUFFER_SIZE)
        data = json.loads(resp.decode())
        device_port = data["body"]
        try:
                int(device_port)
                print("Puerto recibido: {}".format(device_port))
                sockb.close()
                # Ahora se envian los datos de temperatura a la direccion que hemos recibido
                sockd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sockd.connect((IP, int(device_port)))
                i = 0
                while i < NBATCH:
                        temp = str(random.uniform(20, 40))
                        hum = str(random.uniform(30,70))
                        message = json.dumps(create_message(ID, temp, hum))
                        #sockd.send(message.encode())
                        sockd.send(message.encode())
                        print("sent: {}".format(message))
                        time.sleep(FREQUENCE)
                        i += 1
                sockd.close()
        except ValueError:
                print("Recibida respuesta inesperada: {}".format(resp.decode()))