import socket
import threading
import json
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_SERVER = "mail.riskidev.my.id"
SMTP_PORT = 465
SMTP_USERNAME = "server@riskidev.my.id"
SMTP_PASSWORD = "q&nz{V@v4Zt#"

def send_email(to_email, otp):
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = to_email
        msg['Subject'] = "Your OTP Code"

        body = f"Welcome to Pengin Runner Game! Your OTP code is {otp}."
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(SMTP_USERNAME, to_email, msg.as_string())
        server.quit()

        print("Email sent successfully")
    except Exception as e:
        print(f"Failed to send email: {e}")

def generate_otp():
    return str(random.randint(100000, 999999))

class ChatServer:
    def __init__(self, host='0.0.0.0', port=12345):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen(5)
        self.clients = []
        self.leaderboard = []  # [{"username", "score", "id"}]
        self.users = {}  # Global dictionary to store user data
        self.logged_in_users = set()  # Set to track logged in users
        self.lock = threading.Lock()
        self.add_dummy_users()
        self.cmds = [
            'REGISTER',
            'LOGIN',
            'SEND_OTP',
            'RESEND_OTP',
            'START_GAME',
            'UPDATE_SKIN',
            'UPDATE_PROGRESS',
            'LEADERBOARD',
        ]

    def add_dummy_users(self):
        dummy_users = [
            {"username": "alice", "password": "123", "email": "alice@example.com"},
            {"username": "bob", "password": "123", "email": "bob@example.com"},
            {"username": "charlie", "password": "123", "email": "charlie@example.com"}
        ]

        for user in dummy_users:
            self.users[user["username"]] = {
                "password": user["password"],
                "email": user["email"],
                "verified": True,
                "skin_id": 1,
                "otp": None
            }

    def broadcast(self, message):
        with self.lock:
            for client in self.clients:
                try:
                    client.sendall(message.encode('utf-8'))
                except:
                    self.clients.remove(client)

    def handle_client(self, client_socket):
        username = None
        while True:
            try:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break

                command, json_data = data.split(';', 1)
                payload = json.loads(json_data)

                response = self.handle_command(command, payload)
                client_socket.sendall(response.encode('utf-8'))

                if command == 'LOGIN' and json.loads(response.split(';', 1)[1])['success']:
                    username = payload['username']
                    self.logged_in_users.add(username)

            except Exception as e:
                print(f"Error: {e}")
                break

        with self.lock:
            self.clients.remove(client_socket)
            if username:
                self.logged_in_users.remove(username)
        client_socket.close()

    def handle_command(self, command, payload):
        if command == 'LOGIN':
            return self.login(payload)
        elif command == 'REGISTER':
            return self.register(payload)
        elif command == 'RESEND_OTP':
            return self.resend_otp(payload)
        elif command == 'SEND_OTP':  # Corrected here
            return self.send_otp(payload)
        elif command == 'SEND_CHAT':
            return self.send_chat(payload)
        elif command == 'START_GAME':
            return self.create_room(payload)
        elif command == 'UPDATE_SKIN':
            return self.update_skin(payload)
        elif command == 'UPDATE_PROGRESS':
            return self.update_progress(payload)
        else:
            return 'RESPONSE;{"success": false, "message": "Unknown command"}'

    def login(self, payload):
        username = payload.get('username')
        password = payload.get('password')
        
        if not username or not password:
            return 'RESPONSE;{"success": false, "message": "Username and password are required"}'
        
        if username in self.logged_in_users:
            return 'RESPONSE;{"success": false, "message": "User already logged in"}'
        
        if username not in self.users:
            return 'RESPONSE;{"success": false, "message": "User not found"}'
        
        user = self.users[username]
        
        if user['password'] != password:
            return 'RESPONSE;{"success": false, "message": "Incorrect password"}'
        
        if not user['verified']:
            return 'RESPONSE;{"success": false, "message": "Account not verified. Please verify your account first."}'
        
        response = {
            "success": True,
            "message": self.users[username],
        }
        response_json = json.dumps(response)
        return 'LOGIN;' + response_json
    
    def register(self, payload):
        # Handle register
        username = payload['username']
        email = payload['email']
        password = payload['password']
        otp = generate_otp()

        # Check if username already exists
        if username in self.users:
            if self.users[username]['verified']:
                return 'RESPONSE;{"success": false, "message": "Username already exists"}'
            else:
                self.users[username]['otp'] = otp
        else:
            self.users[username] = {
                'skin_id': 1,
                'email': email,
                'password': password,
                'otp': otp,
                'verified': False
            }

        send_email(email, otp)

        return 'RESPONSE;{"success": true, "message": "Registration successful, OTP sent"}'

    def resend_otp(self, payload):
        # Handle resend OTP
        email = payload['email']

        otp = generate_otp()
        send_email(email, otp)

        return 'RESPONSE;{"success": true, "message": "OTP resent"}'

    def send_otp(self, payload):
        username = payload.get('username')
        provided_otp = payload.get('otp')
        
        if not username or not provided_otp:
            return 'RESPONSE;{"success": false, "message": "Username and OTP are required"}'
        
        if username not in self.users:
            return 'RESPONSE;{"success": false, "message": "User not found"}'
        
        user = self.users[username]
        
        if user['verified']:
            return 'RESPONSE;{"success": false, "message": "User is already verified"}'
        
        if user['otp'] == provided_otp:
            user['verified'] = True
            user['otp'] = None  # Clear the OTP after successful verification
            return 'RESPONSE;{"success": true, "message": "OTP verified successfully"}'
        else:
            return 'RESPONSE;{"success": false, "message": "Invalid OTP"}'

    def send_chat(self, payload):
        # Handle send chat
        username = payload['username']
        chat = payload['chat']
        self.broadcast(f"RECEIVE_CHAT;{{\"username\": \"{username}\", \"chat\": \"{chat}\"}}")
        return 'RESPONSE;{"success": true, "message": "Chat sent"}'

    def start_game(self, payload):
        username = payload['username']
        leaderboard_id = len(self.leaderboard) + 1
        self.leaderboard.append({"username": username, "score": 0, "id": leaderboard_id})
        return f'CREATE_ROOM;{{"success": true, "message": "Room created", "leaderboard_id": {leaderboard_id}}}'

    def update_progress(self, payload):
        leaderboard_id = payload['leaderboard_id']
        username = payload['username']
        score = payload['score']

        # Update the user's score in the leaderboard
        for user in self.leaderboard:
            if user['id'] == leaderboard_id and user['username'] == username:
                user['score'] = score
                break

        # Sort the leaderboard by score from biggest to lowest
        self.leaderboard = sorted(self.leaderboard, key=lambda x: x['score'], reverse=True)

        # Find the users with scores above the given score
        user_index = next((index for (index, d) in enumerate(self.leaderboard) if d["username"] == username), None)

        players_with_score_above_user = []
        if user_index > 0:
            players_with_score_above_user = [{'username': self.leaderboard[i]['username'], 'score': self.leaderboard[i]['score'], 'place': i + 1} for i in range(min(2, user_index))]

        self.broadcast_top_10_players()

        response = {
            "success": True,
            "message": "Progress updated",
            "players": players_with_score_above_user
        }
        return 'RESPONSE;' + json.dumps(response)

    def broadcast_top_10_players(self):
        top_10_players = [{'username': user['username'], 'score': user['score'], 'place': idx + 1} for idx, user in enumerate(self.leaderboard[:10])]
        broadcast_message = {
            "message": "Top 10 players updated",
            "players": top_10_players
        }
        self.broadcast(f"LEADERBOARD;{json.dumps(broadcast_message)}")

    def update_skin(self, payload):
        username = payload.get('username')
        skin_id = payload.get('skin_id')

        if not username or skin_id is None:
            return 'RESPONSE;{"success": false, "message": "Username and skin_id are required"}'

        if username not in self.users:
            return 'RESPONSE;{"success": false, "message": "User not found"}'

        self.users[username]['skin_id'] = skin_id

        return 'RESPONSE;{"success": true, "message": "Skin updated"}'

    def start(self):
        print("Server started")
        while True:
            client_socket, addr = self.server.accept()
            print(f"Connection from {addr}")
            with self.lock:
                self.clients.append(client_socket)
            client_handler = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_handler.start()

if __name__ == "__main__":
    server = ChatServer()
    server.start()
