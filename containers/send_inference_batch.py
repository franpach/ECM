# batch mode data inference container

import time
import sys
import threading
import socket
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
nvalues = int(sys.argv[2])
clientid = sys.argv[3]

def run_data_server():
        model = load_model("model.h5")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((dip, dport))
        while True:
                sock.listen(1)
                conn, addr = sock.accept()
                try:
                        numcolumns = len(order)
                        narray = np.empty([nvalues, numcolumns])
                        i = 0
                        while i < nvalues:
                                data = conn.recv(BUFFER_SIZE)
                                json_obj = json.loads(data.decode())
                                if not data: break
                                # comprueba que el id de la conexion es del del cliente
                                if json_obj["id"] != clientid:
                                        conn.close()
                                else:
                                        # si la conexion incluye el id de cliente, se envia a la cola la inferencia
                                        jclient = []
                                        keys_mismatch = 0
                                        # comprueba que las columnas del modelo que ha indicado el cliente con la estructura de los datos enviados por los sensores
                                        for key, value in order.items():
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
                                                # aniade al array de datos el ultimo leido
                                                narray = np.append(narray, xnp, axis=0)
                                        i += 1
                        # cuando se completa el batch indicado, realiza la inferencia
                        score = model.predict(narray, nvalues)
                        print("Tiempo analitica: {}".format(time.time()-ticAnalitica))
                        nalerts = 0
                        # envia un mensaje u otro en funcion del resultado de la inferencia
                        # si hay un unico caso de condiciones inapropiadas se alerta
                        for s in score:
                                if s > 0.5:
                                        nalerts += 1
                        if nalerts > 0:
                                j = {
                                        'msg':"Alerta por condiciones inapropiadas",
                                        'nalerts':nalerts
                                }
                        else:
                                j = {
                                        'msg':"Condiciones apropiadas",
                                        'nalerts':nalerts
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
                        if msg == clientid:
                                while True:
                                        if not q.empty():
                                                d = q.get()
                                                print("Client: recibido {}".format(d))
                                                conn.send(d)
                                                q.task_done()
                        else:
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
