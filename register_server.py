# register server

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
import hashlib

#Constantes del servicio
BOOTSTRAP_FILE = "bootstrap.json" # fichero que guarda la informacion que utiliza el servidor bootstrap
CLIENT_FILE = "clients.json" # fichero que guarda la informacion de todos los clientes
TCP_IP = "127.0.0.1" # IP por defecto donde escucha el servidor
TCP_PORT = 10000 # puerto por defecto donde escucha el servidor
BUFFER_SIZE = 1024 # tamanio maximo del buffer

# Checkea que existen los ficheros necesarios para que el servicio funcione
# Si no existe alguno, lo crea vacio
def check_files():
        if not os.path.isfile(CLIENT_FILE):
                open(CLIENT_FILE, "a").close()
        if not os.path.isfile(BOOTSTRAP_FILE):
                open(BOOTSTRAP_FILE, "a").close()

# Busca el ultimo puerto de rangos asignado para darle el siguiente
# Para cada cliente, nos quedamos con el ultimo puerto del rango
# Returns: El primer puerto para asignar al rango de puertos
def last_range():
        ports = []
        if os.stat(CLIENT_FILE).st_size == 0: # Si el fichero esta vacio se devuelve 5000, el comienzo del primer rango
                port = 5000
        else:
                for client in open(CLIENT_FILE, "r"):
                        c = json.loads(client)
                        range = c["ports"].split("-")
                        ports.append(int(range[1]))
                port = max(ports) + 1
        return port

# Crea el mensaje json que se envia como respuesta al cliente
# Returns: El json enviado como respuesta
def create_response(status, body):
        json_message = {
                "status":status,
                "body":body
        }
        return json_message

# Comprueba que los datos del cliente son validos
# Un nombre es valido si no esta repetido (no existe otro cliente con el mismo nombre)
# Returns: true si ya existe una compania con el nombre solicitado, false en caso contrario
def check_client_data(data):
        found=0
        for client in open(CLIENT_FILE, "r"):
                c = json.loads(client)
                if c["company"] == data["company"]:
                        found=1
        return found

# Crea la informacion del nuevo cliente
# Genera un id mediante un hash con el algoritmo sha1 a raiz del nombre del cliente
# Le asigna un rango de puertos a los que puede conectarse
# Returns: Mensaje json que contiene la informacion del cliente
def create_new_client(data):
        id = hashlib.sha1(data["company"].encode()).hexdigest()
        first_port = last_range()
        last_port = first_port + 9
        range = str(first_port+2)+"-"+str(last_port)
        device_port = first_port
        listening_port = first_port + 1
        client={
                "id":id,
                "company":data["company"],
                "ports":range,
                "device_port":device_port,
                "listening_port":listening_port
        }
        return client

# Registra la informacion del nuevo cliente
def save_client(data):
        data_bootstrap = {
                "id":data["id"],
                "port":data["device_port"]
        }
        with open(BOOTSTRAP_FILE, "a") as bjson_file:
                bjson_file.write(json.dumps(data_bootstrap)+"\n")
        with open(CLIENT_FILE, "a") as cjson_file:
                cjson_file.write(json.dumps(data)+"\n")

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
print("Servidor de registro de clientes conectado. A la espera de datos...")
while(1):
        s.listen(1)
        conn, addr = s.accept()
        try:
                check_files()
                data = conn.recv(BUFFER_SIZE)
                if not data: break
                json_obj = json.loads(data.decode())
                print("Conexion recibida")
                data_ok = check_client_data(json_obj)
                if data_ok == 0:
                        new_client = create_new_client(json_obj)
                        id = new_client["id"]
                        save_client(new_client)
                        body = "Perfil de cliente registrado con exito. ID de identificacion: '{}'.".format(id)
                        status = "OK"
                        message = create_response(status, body)
                        m = json.dumps(message)
                        conn.send(m.encode())
                else:
                        body = "Los datos proporcionados no son validos (nombre repetido)."
                        status = "ERROR"
                        message = json.dumps(create_response(status, body))
                        conn.send(message.encode())
        except Exception as e:
                print(e)
                body = "Ha surgido un error en el proceso de registro de cliente. Intentelo mas adelante, por favor."
                status = "ERROR"
                message = json.dumps(create_response(status, body))
                conn.send(message.encode())
conn.close()