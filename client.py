import socket, threading, struct, os, sys

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

def receive_handler(sock):
    while True:
        msg = recv_msg(sock)
        if not msg:
            print("\n[Server disconnected]")
            os._exit(0)
        
        cmd = msg[:4].decode('utf-8', errors='ignore')
        payload = msg[4:]
        
        if cmd == "CHAT":
            print(f"\n{payload.decode('utf-8', errors='ignore')}\n> ", end="")
        elif cmd == "DRES":
            parts = payload.split(b'|', 1)
            if len(parts) == 2:
                filename = parts[0].decode('utf-8', errors='ignore')
                file_data = parts[1]
                with open(f"client_files/{filename}", "wb") as f:
                    f.write(file_data)
                print(f"\n[Downloaded {filename} successfully]\n> ", end="")
        elif cmd == "ERR ":
            print(f"\n[Error] {payload.decode('utf-8', errors='ignore')}\n> ", end="")

def main():
    host, port = '127.0.0.1', 5000
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host, port))
    except Exception as e:
        print(f"Error connecting to server: {e}")
        return

    threading.Thread(target=receive_handler, args=(sock,), daemon=True).start()
    print("Connected! Commands: /list, /upload <file>, /download <file>, or just type to chat!")
    os.makedirs("client_files", exist_ok=True)
    
    while True:
        try:
            text = input("> ")
            if not text: continue
            
            if text.startswith("/list"):
                send_msg(sock, b"LIST")
            elif text.startswith("/upload "):
                filename = text.split(" ", 1)[1]
                filepath = f"client_files/{filename}"
                if os.path.exists(filepath):
                    with open(filepath, "rb") as f:
                        data = f.read()
                    send_msg(sock, b"UPLD" + filename.encode() + b"|" + data)
                    print(f"[Uploading {filename}...]")
                else:
                    print(f"[File {filename} not found in client_files/]")
            elif text.startswith("/download "):
                filename = text.split(" ", 1)[1]
                send_msg(sock, b"DWNL" + filename.encode())
            else:
                send_msg(sock, b"CHAT" + text.encode())
        except KeyboardInterrupt:
            break
    sock.close()

if __name__ == "__main__":
    main()