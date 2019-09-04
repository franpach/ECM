# custom server

import string
import socket
import argparse
import os
import json
import subprocess
import csv
import math
import random

# Constantes del sistema
RESOURCES_FILE = "resources.csv" # fichero que almacena el uso de los recursos del sistema
TCP_IP = "127.0.0.1" # IP por defecto donde escucha el servidor
TCP_PORT = 10002 # puerto por defecto donde escucha el servidor
BUFFER_SIZE = 1024 # tamanio maximo del buffer
CLIENT_FILE = "clients.json" # fichero que contiene la informacion de los clientes

# Clases para gestionar las excepciones
# error general
class Error(Exception):
        pass
# error cuando el ID del cliente no esta registrado
class NoID(Error):
        pass
# error cuando no hay recursos suficientes para dar cabida al nuevo servicio
class NoCPUAvailable(Error):
        pass
# error cuando no hay puerto disponibles para comunicar al cliente con el contenedor
class NoPort(Error):
        pass
# error cuando el nombre proporcionado de la imagen de docker a descargar no existe
class NoDockerImage(Error):
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

# genera un nuevo nombre para el nuevo servicio
# El algoritmo va generando numeros aleatorios hasta que da con uno que no haya sido asignado a ningun servicio
# se podria hacer consultando todos los servicios parados, con docker ps -a
# Returns: Nombre asignado al nuevo servicio
def new_name():
        found = 1
        while found == 1:
                name = random.randint(0, 10000)
                found = 0
                with open(RESOURCES_FILE, "r") as csv_file:
                        reader = csv.reader(csv_file)
                        for s in reader:
                                if s[0] == name:
                                        found = 1
        return name

# redondea a la baja floats, para que los valores de cpus sean manejables
# Returns: valor float redoneado a la baja
def round_down(n, decimals=0):
        multiplier = 10 ** decimals
        return math.floor(n*multiplier)/multiplier

# incluye en el fichero de uso de cpu el nuevo servicio
def add_service(service):
        with open(RESOURCES_FILE, "a") as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(service)


# actualiza el fichero de uso de cpu en base a un diccionario
def act_file(services):
        with open(RESOURCES_FILE, "w") as csv_file:
                writefile = csv.writer(csv_file)
                for s in services:
                        writefile.writerow(s)

# lee el fichero de uso de cpu para ver como de ocupado esta el sistema
# Returns: CPU disponible, numero de servicios activos y total de CPU que se puede quitar a los servicios
def read_file():
        cpu_total = 4
        cpu_disp = 4
        num_ser = 0
        sum_rest = 0
        if os.path.isfile(RESOURCES_FILE):
                with open(RESOURCES_FILE, "r") as csv_file:
                        reader = csv.reader(csv_file)
                        for service in reader:
                                cpu_disp = cpu_disp - float(service[3])
                                num_ser = num_ser + 1
                                sum_rest = sum_rest + float(service[4])
        else:
                open(RESOURCES_FILE, "a").close()
        return [cpu_disp, num_ser, sum_rest]

# actualiza los recursos del sistema dado el nuevo servicio Returns: CPU asignada al nuevo servicio
# Returns: CPU asignada al nuevo servicio
def actualizar_recursos(json_obj, resources, name):
        new_min = json_obj["cpus"]["min"]
        new_max = json_obj["cpus"]["max"]
        client_id = json_obj["id"]
        cpu_total = 4
        cpu_disp = resources[0]
        num_ser = resources[1]
        sum_rest = resources[2]

        modified_services = []

        # lo primero que hacemos es hacer una copia en un diccionario de cada servicio activo en el sistema
        # sobre esta copia se iran haciendo las modificaciones segun las necesidades del nuevo servicio
        with open(RESOURCES_FILE, "r") as csv_file:
                reader = csv.reader(csv_file)
                for service in reader:
                        modified_services.append(service)

        if new_min < (cpu_disp + sum_rest):
                if new_max <= cpu_disp:
                        new_service = [name,new_min,new_max,new_max,round_down((new_max-new_min),2),client_id,"custom"]
                        add_service(new_service)
                else:
                        # calculamos una media de cuanto podriamos darle (su max - min / 2)
                        new_asig = round_down((new_max + new_min) / 2, 2)
                        if new_asig <= cpu_disp:
                                new_service=[name,new_min,new_max,new_asig,round_down((new_asig-new_min),2),client_id,"custom"]
                        else: # si no se le puede dar una media, se le da min
                                new_asig = new_min
                                # creamos el diccionario del nuevo servicio
                                new_service=[name,new_min,new_max,new_asig,round_down((new_asig-new_min),2),client_id,"custom"]
                                # cuanta cpu falta
                                cpu_needed = new_asig - cpu_disp
                                # cuanto de lo ya asignado hay que quitar a los servicios para dar cabida
                                quitar = round_down(cpu_needed / num_ser, 2)
                                serv_rest = num_ser
                                cpu_rest = cpu_needed
                                while cpu_rest > 0:
                                        with open("resources.csv", "r") as csv_file:
                                                reader = csv.reader(csv_file)
                                                pos = 0 # esta variable marca la posicion del archivo, para mapear el servicio con el del diccionario
                                                for s in reader:
                                                        if float(s[4]) > 0 and cpu_rest > 0:
                                                                if quitar <= float(s[4]):
                                                                        modified_services[pos][3] = round_down(float(s[3])-quitar,2)
                                                                        modified_services[pos][4] = round_down(modified_services[pos][3]-float(s[1]),2)
                                                                        serv_rest = serv_rest - 1
                                                                        cpu_rest = cpu_rest - quitar
                                                                else:   # recalculamos lo que hay que quitar del resto que no se ha podido quitar a este serv
                                                                        quitado = float(s[4])
                                                                        modified_services[pos][3] = round_down(float(s[3])-float(s[4]),2)
                                                                        modified_services[pos][4] = 0
                                                                        serv_rest = serv_rest - 1
                                                                        cpu_rest = cpu_rest - quitado
                                                                        if serv_rest != 0: # cuando todavia quedan servicios por cuadrar
                                                                                quitar = round_down(cpu_rest / serv_rest, 2)
                                                                pos = pos + 1
                                        # actualizamos el fichero para la segunda vuelta tenerlo actualiza
                                        act_file(modified_services)
        add_service(new_service)
        act_services()
        return new_service[3] # devolvemos la cpu asignada finalmente

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
while True:
        s.listen(1)
        print("Servidor conectado. A la espera de datos...")
        conn, addr = s.accept()
        data = conn.recv(BUFFER_SIZE)
        if not data: break
        print("Conexion recibida")
        json_obj = json.loads(data.decode())
        resources = read_file()
        try:
                cpu_min = json_obj["cpus"]["min"]
                cpu_disp = resources[0] + resources[2]
                if cpu_min < cpu_disp:
                        client_found = 0
                        ports_occupied = 0
                        for client in open(CLIENT_FILE, "r"):
                                c = json.loads(client)
                                if c["id"] == json_obj["id"]:
                                        client_found = 1
                                        ports = c["ports"].split("-")
                                        nports = json_obj["nports"]
                                        list_ports_host = []
                                        p = int(ports[0])
                                        i = 0
                                        # para asignar puertos, se buscan nports puertos seguidos dentro del rango de puertos asignados al servicio
                                        # va probando desde el primer puerto del rango, comprobando que esta disponible
                                        # si se encuentra uno ocupado, el recuento vuelve a 0 y se eliminan los puertos ya asignados, y se sigue comprobando por el siguiente
                                        while i < nports and p <= int(ports[1]):
                                                command = "lsof -i:{}".format(p)
                                                try:
                                                        subprocess.check_output(command, shell=True)
                                                        i = 0
                                                        p += 1
                                                        list_ports_host = []
                                                except subprocess.CalledProcessError:
                                                        list_ports_host.append(str(p))
                                                        p += 1
                                                        i += 1
                                        # si al final de recorrer los puertos asignados, el tamanio de la lista no coincide con el numero de puertos asignado, significa que no hay
                                        # nports puertos libres seguidos dentro del rango, por lo que el servicio no puede ser provisto
                                        if len(list_ports_host) != nports:
                                                raise NoPort
                                        else:
                                                if nports > 1:
                                                        str_ports_container = json_obj["lports"][0] + "-" + json_obj["lports"][nports-1]
                                                        str_ports_host = list_ports_host[0] + "-" + list_ports_host[nports-1]
                                                else:
                                                        str_ports_container = json_obj["lports"][0]
                                                        str_ports_host = list_ports_host[0]
                                                print(list_ports_host)
                                                map = str_ports_container + ":" + str_ports_host
                        if client_found == 0:
                                raise NoID
                        image_name = json_obj["service"]["image"]
                        command = "docker pull {}".format(image_name)
                        print(command)
                        try:
                                output = subprocess.check_output(command, shell=True)
                                print(output)
                        except:
                                raise NoDockerImage
                        name = new_name()
                        new_cpu = actualizar_recursos(json_obj, resources, name)
                        command = "docker run --rm -d -t -p {} --name {} --cpus={} {}".format(map, name, new_cpu, image_name)
                        output = subprocess.check_output(command, shell=True)
                        print(output)
                        body = "Puedes conectarte al servicio a traves de los puertos {}. El ID del servicio es {}".format(list_ports_host, name)
                        status = "OK"
                        message = json.dumps(create_response(status, body))
                        conn.send(message.encode())
                else:
                        raise NoCPUAvailable
        except NoID:
                body = "El ID provisto no corresponde con ningun cliente registrado"
                status= "ERROR"
                message = json.dumps(create_response(status, body))
                conn.send(message.encode())
        except NoCPUAvailable:
                body = "No hay espacio suficiente para ejecutar el servicio"
                status= "ERROR"
                message = json.dumps(create_response(status, body))
                conn.send(message.encode())
        except NoPort:
                body = "No hay puertos disponibles para acceder al contenedor"
                status= "ERROR"
                message = json.dumps(create_response(status, body))
                conn.send(message.encode())
        except NoDockerImage:
                body = "No se puede encontrar la imagen proporcionada"
                status = "ERROR"
                message = json.dumps(create_response(status, body))
                conn.send(message.encode())
        except Exception as e:
                print(e)
                body = "Error no controlado"
                status="ERROR"
                message = json.dumps(create_response(status, body))
                conn.send(message.encode())
conn.close()