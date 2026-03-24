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

def broadcast(fd_map, server_fd, sender_fd, msg_bytes):
    for fd, sock in fd_map.items():
        if fd != server_fd and fd != sender_fd:
            try: send_msg(sock, msg_bytes)
            except: pass

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('127.0.0.1', 5000))
    server.listen(5)
    server.setblocking(False)
    
    poll_obj = select.poll()
    poll_obj.register(server.fileno(), select.POLLIN)
    
    fd_map = {server.fileno(): server}
    print("Poll Server listening on port 5000... (Run on Linux/WSL)")
    
    while True:
        events = poll_obj.poll()
        for fd, event in events:
            sock = fd_map[fd]
            
            if sock is server:
                conn, addr = server.accept()
                print(f"Connected: {addr}")
                conn.setblocking(False)
                fd_map[conn.fileno()] = conn
                poll_obj.register(conn.fileno(), select.POLLIN)
            elif event & select.POLLIN:
                try:
                    msg = recv_msg(sock)
                    if not msg: raise Exception("Disconnected")
                    
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
                            broadcast(fd_map, server.fileno(), fd, b"CHAT[Broadcast] User uploaded " + filename.encode())
                    elif cmd == "DWNL":
                        filename = payload.decode('utf-8', errors='ignore')
                        if os.path.exists(f"server_files/{filename}"):
                            with open(f"server_files/{filename}", "rb") as f:
                                send_msg(sock, b"DRES" + filename.encode() + b"|" + f.read())
                        else:
                            send_msg(sock, b"ERR File not found.")
                    elif cmd == "CHAT":
                        broadcast(fd_map, server.fileno(), fd, b"CHAT[Broadcast] " + payload)
                except:
                    print("Client disconnected.")
                    poll_obj.unregister(fd)
                    del fd_map[fd]
                    sock.close()

if __name__ == "__main__":
    main()