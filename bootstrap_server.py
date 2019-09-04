# bootstrap server

import socket
import json

# Crea el mensaje json que se envia como respuesta al cliente
# Returns: json como mensaje de respuesta
def create_response(status, body):
        json_message = {
                "status":status,
                "body":body
        }
        return json_message

IP = ""
PORT = 3000
BOOTSTRAP_FILE = "bootstrap.json"

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((IP, PORT))
print("Servidor bootstrap conectado. A la espera de datos...")
while True:
        sock.listen(1)
        conn, addr = sock.accept()
        try:
                data = conn.recv(1024)
                if not data: break
                print("Conexion recibida")
                found = 0
                for client in open(BOOTSTRAP_FILE, "r"):
                        c = json.loads(client)
                        if c["id"] == data.decode():
                                found = 1
                                port_dest = c["port"]
                                status = "OK"
                                message = json.dumps(create_response(status, str(port_dest)))
                                conn.send(message.encode())
                                print("Sending message")
                                print(message)

                if found==0:
                        body = "ERROR: No existe compania con el ID proporcionado"
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