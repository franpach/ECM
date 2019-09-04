# information server

import string
import socket
import argparse
import os
import json
import subprocess
import csv
import math
import random
import datetime

# Constantes del sistema
RESOURCES_FILE = "resources.csv" # fichero que almacena el uso de los recursos del sistema
TCP_IP = "127.0.0.1" # IP por defecto donde escucha el servidor
TCP_PORT = 5008 # puerto por defecto donde escucha el servidor
BUFFER_SIZE = 1024 # tamanio maximo del buffer
CLIENT_FILE = "clients.json" # Fichero que contiene la informacion de los clientes

#Clases para gestionar las excepciones
# error general
class Error(Exception):
        pass
# error cuando el ID del cliente no esta registrado
class NoID(Error):
        pass

# crea el mensaje json que se envia como respuesta al cliente
# Returns: json como mensaje de respuesta
def create_response(status, body):
        json_message = {
                "status":status,
                "body":body
        }
        return json_message

# devuelve una lista con la informacion de todos los contenedores desplegados por el cliente
# Returns: lista con informacion de servicios
def get_services(clientid):
        services = []
        with open(RESOURCES_FILE, "r") as csv_file:
                reader = csv.reader(csv_file)
                for service in reader:
                        if service[5] == clientid:
                                services.append(service)
        return services

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--port", help="Port to bind to", default=TCP_PORT, type=int)
args=parser.parse_args()

PORT=args.port

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
        try:
                found = 0
                for client in open(CLIENT_FILE, "r"):
                        c = json.loads(client)
                        if c["id"] == clientid:
                                found = 1
                                services = get_services(clientid)
                if found == 0:
                        raise NoID
                if len(services) > 0:
                        num_services = len(services)
                        body = "Tienes {} contenedores ejecutandose: ".format(num_services)
                        for s in services:
                                body += "[ID: {}, CPUs: {}, tipo: {}], ".format(s[0],s[3],s[6])
                        body = body[:-2]
                else:
                        body = "No tienes contenedores ejecutandose en estos momentos"
                status = "OK"
                message = json.dumps(create_response(status, body))
                conn.send(message.encode())
        except NoID:
                body = "El ID provisto no corresponde con ningun cliente registrado"
                status= "ERROR"
                message = json.dumps(create_response(status, body))
                conn.send(message.encode())
        except Exception as e:
                body = "Error no controlado"
                status= "ERROR"
                message = json.dumps(create_response(status, body))
                conn.send(message.encode())
conn.close()