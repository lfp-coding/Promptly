import socket

def send_ipc_command(command) -> bool:
    """
    Send an IPC message to the running instance
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect(("127.0.0.1", 65432))  # Connect to IPC server
            client_socket.sendall(command.encode("utf-8"))
    except ConnectionRefusedError:
        return False
    return True