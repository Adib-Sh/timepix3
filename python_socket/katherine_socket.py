import socket
import struct
import time
import threading

# Constants
CONTROL_PORT = 1555
DATA_PORT = 1556
REMOTE_PORT = 1555

CONTROL_TIMEOUT = 100  # ms
DATA_TIMEOUT = 100  # ms

KATHERINE_CHIP_ID_STR_SIZE = 16

class KatherineUDP:
    def __init__(self):
        self.sock = None
        self.addr_local = None
        self.addr_remote = None
        self.mutex = threading.Lock()

    def init(self, local_port, remote_addr, remote_port, timeout_ms):
        """
        Initialize a UDP session.
        :param local_port: Local port number
        :param remote_addr: Remote IP address
        :param remote_port: Remote port number
        :param timeout_ms: Communication timeout in milliseconds (zero if disabled)
        :return: 0 on success, error code otherwise
        """
        try:
            # Create UDP socket
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            # Bind to local address and port
            self.addr_local = ('0.0.0.0', local_port)
            self.sock.bind(self.addr_local)
            
            # Set socket timeout
            if timeout_ms > 0:
                timeout_sec = timeout_ms / 1000.0
                self.sock.settimeout(timeout_sec)
            
            # Set remote address
            self.addr_remote = (remote_addr, remote_port)
            
            return 0  # Success
        except socket.error as e:
            print(f"Socket error: {e}")
            return e.errno  # Return error code

    def close(self):
        """
        Close the UDP session.
        """
        if self.sock:
            self.sock.close()
            self.sock = None

    def send_exact(self, data):
        """
        Send a message (unreliable).
        :param data: Message data to send
        :return: 0 on success, error code otherwise
        """
        try:
            total_sent = 0
            while total_sent < len(data):
                sent = self.sock.sendto(data[total_sent:], self.addr_remote)
                if sent == 0:
                    raise RuntimeError("Socket connection broken")
                total_sent += sent
            return 0
        except socket.error as e:
            print(f"Failed to send data: {e}")
            return e.errno

    def recv_exact(self, count):
        """
        Receive a message (unreliable).
        :param count: Number of bytes to receive
        :return: Received data on success, None on failure
        """
        try:
            data = bytearray()
            while len(data) < count:
                chunk = self.sock.recv(count - len(data))
                if not chunk:
                    raise RuntimeError("Socket connection broken")
                data.extend(chunk)
            return data
        except socket.error as e:
            print(f"Failed to receive data: {e}")
            return None

    def recv(self, max_count):
        """
        Receive a portion of a message (unreliable).
        :param max_count: Maximum number of bytes to receive
        :return: Received data on success, None on failure
        """
        try:
            data = self.sock.recv(max_count)
            return data
        except socket.error as e:
            print(f"Failed to receive data: {e}")
            return None

    def mutex_lock(self):
        """
        Lock the mutual exclusion synchronization primitive.
        :return: 0 on success, error code otherwise
        """
        self.mutex.acquire()
        return 0

    def mutex_unlock(self):
        """
        Unlock the mutual exclusion synchronization primitive.
        :return: 0 on success, error code otherwise
        """
        self.mutex.release()
        return 0

class KatherineDevice:
    def __init__(self):
        self.control_socket = KatherineUDP()
        self.data_socket = KatherineUDP()

    def init(self, addr):
        """
        Initialize the Katherine device.
        :param addr: IP address of the device
        :return: 0 on success, error code otherwise
        """
        res = self.control_socket.init(CONTROL_PORT, addr, REMOTE_PORT, CONTROL_TIMEOUT)
        if res != 0:
            print("Failed to initialize control socket")
            return res

        res = self.data_socket.init(DATA_PORT, addr, REMOTE_PORT, DATA_TIMEOUT)
        if res != 0:
            print("Failed to initialize data socket")
            self.control_socket.close()
            return res

        return 0  # Success

    def close(self):
        """
        Close the Katherine device sockets.
        """
        self.control_socket.close()
        self.data_socket.close()

    def get_chip_id(self):
        """
        Retrieve the chip ID from the device.
        :return: Chip ID string on success, None on failure
        """
        # Send the echo chip ID command
        res = self.control_socket.send_exact(b'ECHO_CHIP_ID')  # Replace with actual command
        if res != 0:
            print("Failed to send chip ID command")
            return None

        # Receive the response
        crd = self.control_socket.recv_exact(8)
        if crd is None:
            print("Failed to receive chip ID response")
            return None

        # Parse the chip ID
        chip_id = int.from_bytes(crd, byteorder='little')
        x = (chip_id & 0xF) - 1
        y = (chip_id >> 4) & 0xF
        w = (chip_id >> 8) & 0xFFF

        # Format the chip ID string
        chip_id_str = f"{chr(65 + x)}{y}-W000{w}"
        return chip_id_str

# Example usage
if __name__ == "__main__":
    device = KatherineDevice()
    device_ip = "192.168.1.218"  # Replace with the actual device IP

    if device.init(device_ip) == 0:
        print("Katherine device initialized successfully")

        # Get the chip ID
        chip_id = device.get_chip_id()
        if chip_id:
            print(f"Chip ID: {chip_id}")
        else:
            print("Failed to retrieve chip ID")

        device.close()
    else:
        print("Failed to initialize Katherine device")