import socket, select, struct, os

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

def broadcast(inputs, server_socket, sender_sock, msg_bytes):
    for s in inputs:
        if s is not server_socket and s is not sender_sock:
            try: send_msg(s, msg_bytes)
            except: pass

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('127.0.0.1', 5000))
    server.listen(5)
    
    inputs = [server]
    print("Select Server listening on port 5000...")
    
    while True:
        read_ready, _, _ = select.select(inputs, [], [])
        for sock in read_ready:
            if sock == server:
                client, addr = server.accept()
                print(f"Connected: {addr}")
                inputs.append(client)
            else:
                msg = recv_msg(sock)
                if msg:
                    cmd = msg[:4].decode('utf-8', errors='ignore')
                    payload = msg[4:]
                    if cmd == "LIST":
                        files = os.listdir("server_files")
                        send_msg(sock, b"CHAT[Server Files]\n" + ("\n".join(files) if files else "No files.").encode())
                    elif cmd == "UPLD":
                        parts = payload.split(b'|', 1)
                        if len(parts) == 2:
                            filename = parts[0].decode('utf-8', errors='ignore')
                            with open(f"server_files/{filename}", "wb") as f: f.write(parts[1])
                            broadcast(inputs, server, sock, b"CHAT[Broadcast] User uploaded " + filename.encode())
                    elif cmd == "DWNL":
                        filename = payload.decode('utf-8', errors='ignore')
                        if os.path.exists(f"server_files/{filename}"):
                            with open(f"server_files/{filename}", "rb") as f:
                                send_msg(sock, b"DRES" + filename.encode() + b"|" + f.read())
                        else:
                            send_msg(sock, b"ERR File not found.")
                    elif cmd == "CHAT":
                        broadcast(inputs, server, sock, b"CHAT[Broadcast] " + payload)
                else:
                    print(f"Disconnected: {sock.getpeername()}")
                    inputs.remove(sock)
                    sock.close()

if __name__ == "__main__":
    main()