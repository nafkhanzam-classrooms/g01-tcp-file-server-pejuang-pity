import socket, struct, os

os.makedirs("server_files", exist_ok=True)

def send_msg(sock, data):
    header = struct.pack(">I", len(data))
    sock.sendall(header + data)

def recv_all(sock, n):
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet: return None
        data.extend(packet)
    return bytes(data)

def recv_msg(sock):
    header = recv_all(sock, 4)
    if not header: return None
    length = struct.unpack(">I", header)[0]
    return recv_all(sock, length)

def handle_protocol(sock, msg):
    cmd = msg[:4].decode('utf-8', errors='ignore')
    payload = msg[4:]
    
    if cmd == "LIST":
        files = os.listdir("server_files")
        file_list = "\n".join(files) if files else "No files on server."
        send_msg(sock, b"CHAT[Server Files]\n" + file_list.encode())
    elif cmd == "UPLD":
        parts = payload.split(b'|', 1)
        if len(parts) == 2:
            filename = parts[0].decode('utf-8', errors='ignore')
            with open(f"server_files/{filename}", "wb") as f:
                f.write(parts[1])
            send_msg(sock, b"CHAT[Broadcast] You uploaded " + filename.encode())
    elif cmd == "DWNL":
        filename = payload.decode('utf-8', errors='ignore')
        filepath = f"server_files/{filename}"
        if os.path.exists(filepath):
            with open(filepath, "rb") as f:
                send_msg(sock, b"DRES" + filename.encode() + b"|" + f.read())
        else:
            send_msg(sock, b"ERR File not found.")
    elif cmd == "CHAT":
        send_msg(sock, b"CHAT[Broadcast (Sync is solo)] " + payload)

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('127.0.0.1', 5000))
    server.listen(5)
    print("Sync Server listening on port 5000...")
    
    while True:
        conn, addr = server.accept()
        print(f"Connected: {addr}")
        while True:
            msg = recv_msg(conn)
            if not msg:
                print(f"Disconnected: {addr}")
                break
            handle_protocol(conn, msg)
        conn.close()

if __name__ == "__main__":
    main()