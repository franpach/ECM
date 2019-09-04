# service remove server

import string
import socket
import os
import json
import subprocess
import csv
import math

RESOURCES_FILE = "resources.csv" # fichero que almacena el uso de los recursos del sistema
TCP_IP = "127.0.0.1" # IP por defecto donde escucha el servidor
TCP_PORT = 12000 # puerto por defecto donde escucha el servidor
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
                found = 0
                services = []
                num_services = 0
                with open(RESOURCES_FILE, "r") as csv_file:
                        reader = csv.reader(csv_file)
                        for s in reader:
                                if int(s[0]) == serviceid:
                                        found = 1
                                        cpu_free = float(s[3])
                                else:
                                        num_services += 1
                                        services.append(s)
                if found == 0:
                        raise NoService
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
                command = "docker stop {}".format(serviceid)
                subprocess.check_output(command, shell=True)
                command = "docker rm {}".format(serviceid)
                subprocess.check_output(command, shell=True)
                body = "El servicio {} ha sido eliminado correctamente".format(serviceid)
                status = "OK"
                message = json.dumps(create_response(status, body))
                conn.send(message.encode())
        except NoID:
                body = "El ID provisto no corresponde con ningun cliente registrado"
                status = "ERROR"
                message = json.dumps(create_response(status, body))
                conn.send(message.encode())
        except NoService:
                body = "El ID de servicio no existe"
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
