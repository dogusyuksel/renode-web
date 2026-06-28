import time
import socket
import threading

COMMANDS = {
    "SET_LOG_DEBUG": [0x01, 0x06, 0x04, 0x02, 0x00, 0x01, 0xE8, 0xFA],
    "SET_TPS_ENABLE_0": [0x01, 0x06, 0x04, 0x01, 0x00, 0x00, 0xD9, 0x3A],
    "SET_TPS_ENABLE_1": [0x01, 0x06, 0x04, 0x01, 0xFF, 0xFF, 0xD8, 0x8A]
}


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

    def send(self, cmd_name):
        if cmd_name not in COMMANDS:
            raise ValueError(f"Unknown command: {cmd_name}")

        payload = bytes(COMMANDS[cmd_name])

        print(
            "[TX]",
            cmd_name,
            ":",
            " ".join(f"{b:02X}" for b in payload)
        )

        self.sock.sendall(payload)

    def close(self):
        self.sock.close()


# Logic

mb = ModbusClient("localhost", 1234)

mb.send("SET_LOG_DEBUG")

time.sleep(2)
mb.send("SET_TPS_ENABLE_1")

time.sleep(2)
mb.send("SET_TPS_ENABLE_0")

time.sleep(20)

mb.close()
