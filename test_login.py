import socket
import json

def test_login(username, password):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('127.0.0.1', 5555))
    
    # test send
    login_info = json.dumps({"username": username, "password": password})
    client.send(login_info.encode('utf-8'))

    response = client.recv(1024).decode('utf-8')
    response_data = json.loads(response)
    print(f"[SERVER RESPONSE] {response_data}")

    client.close()

# Test different login scenarios
test_login("player1", "qwerty")
test_login("player1", "test")
test_login("deeznuts", "test")
