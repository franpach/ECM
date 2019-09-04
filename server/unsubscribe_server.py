# unsubscription server

import string
import socket
import argparse
import os
import json
import subprocess
import csv
import math

# Constantes del servicio
BOOTSTRAP_FILE = "bootstrap.json" # fichero que guarda la informacion que utiliza el servidor bootstrap
CLIENT_FILE = "clients.json" # fichero que guarda la informacion de todos los clientes
RESOURCES_FILE = "resources.csv" # fichero que almacena el uso de los recursos del sistema
TCP_IP = "127.0.0.1" # IP por defecto donde escucha el servidor
TCP_PORT = 10001 # puerto por defecto donde escucha el servidor
BUFFER_SIZE = 1024 # tamanio maximo del buffer

# Clases para gestionar las excepciones
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

# actualiza los contenedores corriendo con las nuevas cpu asignadas
def act_services():
        with open(RESOURCES_FILE, "r") as csv_file:
                reader = csv.reader(csv_file)
                for s in reader:
                        command = "docker ps --filter 'name=^/{}$' --format '{{.ID}}'".format(s[0])
                        service_id = subprocess.check_output(command, shell=True) # sacamos el ID del contenedor
                        # puede suceder que el servicio deje de funcionar antes de actualizarlo, entonces el ps devuelve valor vacio y no se actualiza nada
                        if service_id.decode() != "":
                                command = "docker update {} --cpus={}".format(s[0], s[3])
                                output = subprocess.check_output(command, shell=True)

# actualiza el fichero de uso de cpu en base a un diccionario
def act_file(services):
        with open(RESOURCES_FILE, "w") as csv_file:
                writefile = csv.writer(csv_file)
                for s in services:
                        writefile.writerow(s)

# redondea a la baja flaots, para que los valores de cpus sean manejables
def round_down(n, decimals=0):
        multiplier = 10 ** decimals
        return math.floor(n*multiplier)/multiplier

# Comprueba si el cliente existe o no
# Returns: 1 si existe, 0 si no
def check_client(clientid):
        found = 0
        for client in open(CLIENT_FILE, "r"):
                c = json.loads(client)
                if c["id"] == clientid:
                        found = 1
        return found

# Elimina los servicios que tiene levantados el cliente
def remove_services(clientid):
        services = []
        cpu_free = 0
        num_services = 0
        with open(RESOURCES_FILE, "r") as csv_file:
                reader = csv.reader(csv_file)
                for s in reader:
                        if s[5] == clientid:
                                cpu_free = float(s[3])
                                command = "docker stop {}".format(s[0])
                                subprocess.check_output(command, shell=True)
                                command = "docker rm {}".format(s[0])
                                subprocess.check_output(command, shell=True)
                        else:
                                num_services += 1
                                services.append(s)
        if num_services > 0:
                add_each = round_down(cpu_free/num_services,2)
                for s in services:
                        if s[3] < s[2]:
                                if float(s[2]) <= add_each:
                                        s[3] = round_down(float(s[3]) + (float(s[2]) - float(s[3])),2)
                                else:
                                        s[3] = round_down(float(s[3]) + add_each,2)
                                s[4] = round_down(float(s[3]) - float(s[1]),2)
        act_file(services)
        act_services()

# Elimina al cliente del fichero de clientes
def remove_client(clientid):
        clients = []
        for client in open(CLIENT_FILE, "r"):
                c = json.loads(client)
                if c["id"] != clientid:
                        clients.append(c)
        with open(CLIENT_FILE, "w") as cjson_file:
                for c in clients:
                        cjson_file.write(json.dumps(c)+"\n")
        clients = []
        for client in open(BOOTSTRAP_FILE, "r"):
                c = json.loads(client)
                if c["id"] != clientid:
                        clients.append(c)
        with open(BOOTSTRAP_FILE, "w") as bjson_file:
                for c in clients:
                        bjson_file.write(json.dumps(c)+"\n")

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((TCP_IP, TCP_PORT))
print("Servidor conectado. A la espera de datos...")
while True:
        sock.listen(1)
        conn, addr = sock.accept()
        try:
                data = conn.recv(BUFFER_SIZE)
                if not data: break
                print("Conexion recibida")
                json_obj = json.loads(data.decode())
                clientid = json_obj["id"]
                if check_client(clientid) == 1:
                        remove_services(clientid)
                        remove_client(clientid)
                        body = "Tu cuenta ha sido existosamente eliminada"
                        status = "OK"
                        message = json.dumps(create_response(status, body))
                        conn.send(message.encode())
                else:
                        raise NoID
        except NoID:
                body = "El ID provisto no corresponde con ningun cliente registrado"
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
