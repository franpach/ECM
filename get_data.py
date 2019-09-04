# listening container server

import threading
import socket
import time
import queue
import json
import sys

BUFFER_SIZE=1024

dip = "0.0.0.0"
dport = 10000
cip = "0.0.0.0"
cport = 10001

clientid = sys.argv[1]

def run_data_server():
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.bind((dip, dport))
                while True:
                        s.listen(1)
                        conn,addr = s.accept()
                        try:
                                while True:
                                        data = conn.recv(BUFFER_SIZE)
                                        print("Conexion recibida: {}".format(data.decode()))
                                        json_obj = json.loads(data.decode())
                                        if not data: break
                                        # comprueba que el id de la conexion es el del cliente
                                        if json_obj["id"] != clientid:
                                                conn.close()
                                        else:
                                                # si la conexion incluye el id de cliente, se envia a la cola el json con los datos
                                                jclient = {}
                                                for key, value in json_obj.items():
                                                        if key != "id":
                                                                jclient.update({key:value})
                                                msg = json.dumps(jclient)
                                                q.put(msg.encode())
                        except Exception as e:
                                print(e)
                                conn.close()

def run_client_server():
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.bind((cip, cport))
                while True:
                        s.listen(1)
                        conn,addr=s.accept()
                        try:
                                data = conn.recv(1024)
                                msg = data.decode()
                                # comprueba que el id de la conexion es el del cliente
                                if msg == clientid:
                                        while True:
                                                # lee los datos de la cola mientras haya
                                                if not q.empty():
                                                        d = q.get()
                                                        print("Cliente: recibido {}".format(d))
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