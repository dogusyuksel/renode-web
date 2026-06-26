import time
import socket
import threading

class ModbusClient:
    def __init__(self, host="localhost", port=1234):
        self.sock = socket.create_connection((host, port))

        self.rx_thread = threading.Thread(
            target=self._rx_loop,
            daemon=True
        )
        self.rx_thread.start()

    def _rx_loop(self):
        buffer = ""

        while True:
            try:
                data = self.sock.recv(4096)

                if not data:
                    print("[RX] disconnected")
                    break

                buffer += data.decode("ascii", errors="replace")

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)

                    line = line.rstrip("\r")

                    if line:
                        print(f"[RX] {line}")

            except Exception as e:
                print("[RX ERROR]", e)
                break

    def close(self):
        self.sock.close()


# Logic

mb = ModbusClient("localhost", 1234)


time.sleep(20)

mb.close()
