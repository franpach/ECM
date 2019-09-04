# one to one mode data inference container

import sys
import threading
import socket
import time
import queue
import json
from keras.models import load_model
import numpy as np

BUFFER_SIZE = 1024

dip = "0.0.0.0"
dport = 10000
cip = "0.0.0.0"
cport = 10001

order = eval(sys.argv[1])
clientid = sys.argv[2]

def run_data_server():
        model = load_model("model.h5")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((dip, dport))
        while True:
                s.listen(1)
                conn, addr = s.accept()
                try:
                        while True:
                                data = conn.recv(BUFFER_SIZE)
                                print("Data recibido: {}".format(data.decode()))
                                json_obj = json.loads(data.decode())
                                if not data: break
                                # comprueba que el id de la conexion el del cliente
                                if json_obj["id"] != clientid:
                                        conn.close()
                                else:
                                        # si la conexion incluye el id de cliente, se envia a la cola la inferencia
                                        jclient = []
                                        keys_mismatch = 0
                                        # comprueba que las columnas del modelo que ha indicado el cliente corresponden con la estructura de los datos enviados por los sensores
                                        for key, value in order.items():
                                                print(key)
                                                if not value in json_obj.keys():
                                                        keys_mismatch = 1
                                                else:
                                                        jclient.append(float(json_obj[value]))
                                        if keys_mismatch == 1:
                                                print("ERROR en claves")
                                                j = {
                                                        'msg':"ERROR. Desajuste de claves"
                                                }
                                        # si no hay error con las claves realiza el analisis
                                        else:
                                                # genera el array de datos a analizar
                                                xnp = np.array([jclient])
                                                score = model.predict_classes(xnp)
                                                # envia un mensaje u otro en funcion del resultado de la inferencia
                                                if score == 1:
                                                        j = {
                                                                'temp':json_obj["temp"],
                                                                'hum':json_obj["hum"],
                                                                'msg':"Alerta por condiciones inapropiadas"
                                                        }
                                                else:
                                                        j = {
                                                                'temp':json_obj["temp"],
                                                                'hum':json_obj["hum"],
                                                                'msg':"Condiciones apropiadas"
                                                        }
                                        msg = json.dumps(j)
                                        q.put(msg.encode())
                except Exception as e:
                        print(e)
                        conn.close()

def run_client_server():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((cip, cport))
        while True:
                s.listen(1)
                conn, addr = s.accept()
                try:
                        data = conn.recv(BUFFER_SIZE)
                        msg = data.decode()
                        # comprueba que el id de la conexion es el del cliente
                        if msg == clientid:
                                while True:
                                        # lee los datos de la cola mientras haya
                                        if not q.empty():
                                                d = q.get()
                                                print("Client: recibido {}".format(d))
                                                conn.send(d)
                                                q.task_done()
                        else:
                                print("Connection not allowed")
                                msg = "ERROR. Conexion no permitida"
                                conn.send(msg.encode())
                                conn.close()
                except Exception as e:
                        print(e)
                        conn.close()

q = queue.Queue()
# inicia el thread que escucha las conexiones de los sensores
td = threading.Thread(target=run_data_server)
# inicia el thread que escucha las conexiones de los clientes
tc = threading.Thread(target=run_client_server)
td.start()
tc.start()
q.join()