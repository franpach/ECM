# service stop server

import string
import socket
import os
import json
import subprocess
import csv

RESOURCES_FILE = "resources.csv" # fichero que almacena el uso de los recursos del sistema
TCP_IP = "127.0.0.1" # IP por defecto donde escucha el servidor
TCP_PORT = 5013 # puerto por defecto donde escucha el servidor
BUFFER_SIZE = 1024 # tamanio maximo del buffer
CLIENT_FILE = "clients.json" # fichero que contiene la informacion de los clientes

# Clases para gestionar las excepciones
# error general
class Error(Exception):
        pass

# error cuando el ID del cliente no esta registrado
class NoID(Error):
        pass

# error cuando el servicio indicado no existe
class NoService(Error):
        pass

# crea el mensaje json que se envia como respuesta al cliente
def create_response(status, body):
        json_message = {
                "status":status,
                "body":body
        }
        return json_message

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((TCP_IP, TCP_PORT))
while True:
        sock.listen(1)
        print("Servidor conectado. A la espera de datos...")
        conn, addr = sock.accept()
        data = conn.recv(BUFFER_SIZE)
        if not data: break
        print("Conexion recibida")
        json_obj = json.loads(data.decode())
        clientid = json_obj["id"]
        serviceid = json_obj["serviceid"]
        try:
                found = 0
                for client in open(CLIENT_FILE, "r"):
                        c = json.loads(client)
                        if c["id"] == clientid:
                                found = 1
                if found == 0:
                        raise NoID
                command = "docker ps --filter 'name=^/{}$' --format '{{.ID}}'".format(serviceid)
                service_id = subprocess.check_output(command, shell=True)
                if service_id.decode() == "":
                        raise NoService
                else:
                        command = "docker stop {}".format(serviceid)
                        subprocess.check_output(command, shell=True)
                body = "El servicio {} ha sido parado correctamente".format(serviceid)
                status = "OK"
                message = json.dumps(create_response(status, body))
                conn.send(message.encode())
        except NoID:
                body = "El ID provisto no corresponde con ningun cliente registrado"
                status = "ERROR"
                message = json.dumps(create_response(status, body))
                conn.send(message.encode())
        except NoService:
                body = "No hay un servicio ejecutandose con ID {}".format(serviceid)
                status = "ERROR"
                message = json.dumps(create_response(status, body))
                conn.send(message.encode())
        except Exception as e:
                print(e)
                body = "Error no controlado"
                status = "ERROR"
                message = json.dumps(create_response(status, body))
                conn.send(message.encode())
conn.close()
