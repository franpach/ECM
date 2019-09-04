import socket
import argparse
import json
import time
import os
import ast

# comprueba que el fichero que contiene el modleo existe
def check_model(file):
        if os.path.isfile(file):
                if file[-3:] != ".h5":
                        ok = 0
                else:
                        ok = 1
        else:
                ok = 0
        return ok

# comprueba que el diccionario que provee el cliente esta bien formateado
# para estar correcto, todas las claves han de ser enteros, y los literales estar entre comillas simples
def check_order(order):
        ok = 1
        try:
                quotes = order.find('"')
                if quotes != -1:
                        ok = 0
                else:
                        dict = ast.literal_eval(order)
                        for k in dict.keys():
                                int(k)
        except Exception as e:
                print(e)
                ok = 0
        return ok


# comprueba que los puertos estan bien formateados
def check_ports(LPORTS, NPORTS):
        if NPORTS == len(LPORTS):
                try:
                        i=1
                        ok=1
                        int(LPORTS[0])
                        while i < len(LPORTS) and ok==1:
                                if int(LPORTS[i]) != int(LPORTS[i-1])+1:
                                        ok=0
                                i+=1
                except ValueError:
                        ok=0
                print("puertos correctos: {}".format(ok))
        else:
                ok = 0
        return ok

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--mincpus", help="Min CPUs to assign to the image", default=0.5, type=float)
parser.add_argument("-m", "--maxcpus", help="Max CPUs to assign to the image", default=1, type=float)
parser.add_argument("-p", "--personalised", help="1 if the image is given by the client", default=0, type=int)
parser.add_argument("-s", "--service", help="Service to deploy", default="default")
parser.add_argument("-f", "--file", help="File with model", default="null")
parser.add_argument("-v", "--values", help="Values to be analyse", default="./data/temp.csv")
parser.add_argument("-i", "--image", help="Image of the docker container to be downloaded", default="null")
parser.add_argument("-l", "--lports", help="List of open ports from container", default="default")
parser.add_argument("-n", "--nports", help="Number of ports to be openened", default=1, type=int)
parser.add_argument("-w", "--id", help="Client ID", default="null")
parser.add_argument("-o", "--order", help="For analysis service, order of columns that the model follows", default="null")
parser.add_argument("-b", "--batch", help="Batch processing in analysis service")
parser.add_argument("-k", "--nbatch", help="Number of values to be processed in batch mode in analysis service", default=10, type=int)
parser.add_argument("-r", "--removed_service", help="Service to be removed", default=0, type=int)
args=parser.parse_args()

ERROR=0
BUFFER_SIZE=1024
TCP_IP="127.0.0.1"
SERVICE=args.service.lower()
MINCPUS=args.mincpus
MAXCPUS=args.maxcpus
FILE=args.file
DATA=args.values
IMAGE=args.image
PERSONALISED=args.personalised
LPORTS=args.lports.split(",")
NPORTS=args.nports
ID = args.id
ORDER = args.order
FILE_NAME = args.file
NBATCH = args.nbatch
RSERVICE = args.removed_service
if args.batch:
        BATCH = 1
else:
        BATCH = 0

if ID == "null":
        ERROR = 1
        print("ERROR. Has de proveer obligatoriamente una identificacion de cliente")
else:
        if MINCPUS >= 2 or MINCPUS <= 0:
                print("WARNING. Solo puede utilizar hasta 2 CPUs. Asignando CPUs minimas por defecto (0.5)...")
                MINCPUS=0.5
        if MAXCPUS>=2 or MAXCPUS<=0:
                print("WARNING. Solo puede utilizar hasta 2 CPUs. Asignando CPUs maximas por defecto (1)...")
                MAXCPUS=1

        if NPORTS <= 0 or NPORTS > 8:
                print("WARNING. Solo pueden abrirse entre 1 y 8 puertos. Asignando puertos por defecto (1)...")
                NPORTS = 1

        if PERSONALISED==1:
                if IMAGE == "null":
                        print("ERROR. Se ha indicado servicio personalizado pero no se aporta imagen")
                        ERROR=1
                else:
                        SERVICE="personalised service"
                if LPORTS[0]=="default":
                        print("ERROR. Tienes que proveer puertos de escucha")
                        ERROR = 1
                else:
                        ports_ok = check_ports(LPORTS, NPORTS)
                        if ports_ok == 0:
                                print("ERROR. La lista de puertos debe contener enteros seguidos y su longitud coincidir con el parametro nports")
                                ERROR = 1
                PORT = 10002
        else:
                if SERVICE == "default":
                        print("ERROR. Se ha indicado servicio por defecto pero no se indica cual")
                        ERROR=1
                else:
                        if SERVICE=="analisis":
                                PORT=5005
                                if ORDER == "null" or FILE == "null":
                                        print("ERROR. Ha de proveerse un orden de columnas para que el modelo proporcionado las estudie, y un modelo en un fichero .h5")
                                        ERROR = 1
                                else:
                                        order_ok = check_order(ORDER)
                                        model_ok = check_model(FILE)
                                        if order_ok == 0:
                                                print("ERROR. El diccionario que contiene el orden de columnas no esta bien definido")
                                                print("El parametro ha de tener la forma \"{<int>:'value'}\"")
                                                ERROR = 1
                                        if model_ok == 0:
                                                print("ERROR. Has de proveer un fichero valido")
                                                ERROR = 1
                                        else:
                                                f = open(FILE, "r")
                                        try:
                                                int(NBATCH)
                                        except ValueError:
                                                print("WARNING. El numero de valores a procesar tiene que ser un entero. Asignando por defecto (10)...")
                                                NBATCH = 10
                        elif SERVICE=="listening":
                                PORT=5006
                        elif SERVICE=="debug":
                                PORT=5010
                        elif SERVICE=="info":
                                PORT= 5008
                        elif SERVICE=="delete":
                                if RSERVICE == 0:
                                        print("ERROR. Has de proveer un ID de servicio")
                                        ERROR = 1
                                else:
                                        PORT = 12000
                        elif SERVICE=="stop":
                                if RSERVICE == 0:
                                        print("ERROR. Has de proveer un ID de servicio")
                                        ERROR = 1
                                else:
                                        PORT = 5013
                        elif SERVICE == "unsubscribe":
                                PORT = 10001
                        else:
                                PORT=5007

if ERROR == 0:
        json_message = {
                'id':ID,
                'cpus' : {
                        'min':MINCPUS,
                        'max':MAXCPUS
                },
                'lports':LPORTS,
                'nports':NPORTS,
                'data' : DATA,
                'service': {
                        'custom':PERSONALISED,
                        'image':IMAGE,
                        'default_service':SERVICE
                },
                'order':ORDER,
                'batch':BATCH,
                'number_values':NBATCH,
                'serviceid':RSERVICE
        }
        MESSAGE = json.dumps(json_message)
        print(MESSAGE)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((TCP_IP, PORT))
        sock.send(MESSAGE.encode())
        t2 = time.time()
        if SERVICE == "analisis":
                resp = sock.recv(BUFFER_SIZE)
                if resp.decode() == "model":
                        print("Now sending file")
                        f = open(FILE_NAME, 'rb')
                        l = f.read(BUFFER_SIZE)
                        while(l):
                                sock.send(l)
                                l = f.read(1024)
                        f.close()
                        print("Now waiting for response")
                        resp = sock.recv(BUFFER_SIZE)
                        print("Received resp: {}".format(resp))
                else:
                        print(resp.decode())
                print("Tiempo envio modelo :{}".format(time.time()-t2))
        else:
                print("Now waiting for response")
                resp = sock.recv(BUFFER_SIZE)
                print("Received resp: {}".format(resp))
        sock.close()
