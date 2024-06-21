import socket
import threading
import json

users = {
    "player1": "qwerty",
    "player2": "qwerty",
    "player3": "qwerty"
}

# endpoint to login
def handle_client(client_socket, client_address):
    print(f"[NEW CONNECTION] {client_address} connected.")
    try:
        while True:
            # get login data
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break
            print(f"[RECEIVED] {data} from {client_address}")

            try:
                login_data = json.loads(data)
                username = login_data.get("username")
                password = login_data.get("password")

                if username in users and users[username] == password:
                    response = {"status": "success", "message": "LOGIN SUCCESS"}
                else:
                    response = {"status": "fail", "message": "LOGIN FAILED"}
            except json.JSONDecodeError:
                response = {"status": "error", "message": "Invalid JSON"}
            client_socket.send(json.dumps(response).encode('utf-8'))

    except Exception as e:
        print(f"[EXCEPTION] {e}")
    finally:
        print(f"[DISCONNECTED] {client_address} disconnected.")
        client_socket.close()

def start_server(host='127.0.0.1', port=5555):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"[LISTENING] Server is listening on {host}:{port}")

    while True:
        client_socket, client_address = server.accept()
        client_handler = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_handler.start()

if __name__ == "__main__":
    start_server()
