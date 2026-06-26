import sys
import os
import json
from graphviz import Digraph

resc_string = ""
repl_string = ""

with open("./uploads/structure.json", "r") as f:
    data = json.load(f)

# lets create both files' content
repl_string += f'''using "/workspace/extendedcpus/{data["mcu"].lower()}.repl"\n'''
repl_string += """
flashMem: Memory.MappedMemory
    size: 0x10000\n
"""

verbose = "false"

if sys.argv[1] == "log_enable":
    verbose = "true"

resc_string += f'''
include "/workspace/support/STM32F103_RCC.cs"
include "/workspace/support/STM32L4_RCC.cs"
include "/workspace/support/STML4_I2C.cs"

using sysbus
mach create
machine LoadPlatformDescription @/workspace/uploads/example.repl
sysbus.cpu LogFunctionNames {verbose}
'''

button_substring = ""
counter = 0
telnet_port = 1234
it_has_i2c = False
it_has_spi = False
it_has_led = False
it_has_cs = False
it_has_button = False
for item in data["connections"]:
    if item["peripheral"].upper().startswith("I2C") and not it_has_i2c:
        it_has_i2c = True
        if not os.path.islink(f"/workspace/peripherals/i2c/{item['sensor']}.cs"):
            resc_string = f'include "/workspace/peripherals/i2c/{item["sensor"]}.cs"\n' + resc_string # write at the beginning
        resc_string += f'logLevel -1 sysbus.{item["peripheral"].lower()}\n'
        if not os.path.islink(f"/workspace/peripherals/i2c/{item['sensor']}.cs"):
            repl_string += f'{item["sensor"]}: Antmicro.Renode.Peripherals.I2C.{item["sensor"]} @ {item["peripheral"].lower()} {item["slaveId"]}\n'
        else:
            repl_string += f'{item["sensor"]}: I2C.{item["sensor"]} @ {item["peripheral"].lower()} {item["slaveId"]}\n'
    if item["peripheral"].upper().startswith("SPI") and not it_has_spi:
        it_has_spi = True
        if not os.path.islink(f"/workspace/peripherals/spi/{item['sensor']}.cs"):
            resc_string = f'include "/workspace/peripherals/spi/{item["sensor"]}.cs"\n' + resc_string # write at the beginning
        resc_string += f'logLevel -1 sysbus.{item["peripheral"].lower()}.{item["sensor"]}\n'
        if not os.path.islink(f"/workspace/peripherals/spi/{item['sensor']}.cs"):
            repl_string += f"""
{item["sensor"]}: Antmicro.Renode.Peripherals.SPI.{item["sensor"]} @ {item["peripheral"].lower()}
    memory: flashMem
"""
        else:
            repl_string += f"""
{item["sensor"]}: SPI.{item["sensor"]} @ {item["peripheral"].lower()}
    memory: flashMem
"""
    if item["peripheral"].upper().startswith("GPIO"):
        counter += 1
        resc_string = f'include "/workspace/peripherals/gpio/{item["sensor"]}.cs"\n' + resc_string # write at the beginning
        if item["sensor"].upper().startswith("LED"):
            it_has_led = True
        if item["sensor"].upper().startswith("CS"):
            it_has_cs = True
        if item["sensor"].upper().startswith("BUTTON"):
            it_has_button = True
            button_substring += f"""
sleep 2
sysbus.{item["port"]}.{item["sensor"]}{str(counter)} PressAndRelease
"""
            repl_string += f"""
{item["sensor"]}{str(counter)}: Antmicro.Renode.Peripherals.Miscellaneous.{item["sensor"]} @ {item["port"]}
    -> {item["port"]}@{item["pin"]}
"""
        else:
            resc_string += f'logLevel -1 {item["port"]}.{item["sensor"]}{str(counter)}\n'
            repl_string += f"""
{item["sensor"]}{str(counter)}: Antmicro.Renode.Peripherals.Miscellaneous.{item["sensor"]} @ {item["port"]}
{item["port"]}:
    {item["pin"]} -> {item["sensor"]}{str(counter)}@0
"""

    if item["peripheral"].upper().startswith("UART") or item["peripheral"].upper().startswith("USART"):
        resc_string += f'showAnalyzer {item["peripheral"].lower()}\n'
        resc_string += f'emulation CreateServerSocketTerminal {telnet_port} "{item["peripheral"].upper()}" false\n'
        resc_string += f'connector Connect sysbus.{item["peripheral"].lower()} {item["peripheral"].upper()}\n'
        telnet_port = telnet_port + 1


resc_string += """
machine StartGdbServer 3333 true
macro reset
\"\"\"
    sysbus LoadELF @/workspace/uploads/firmware.elf
\"\"\"
runMacro $reset
start
"""

if it_has_button:
    resc_string += button_substring + "\n"

resc_string += """
"""


resc_string = """
logFile @/workspace/uploads/log.txt
""" + resc_string + "\n"

print(repl_string)
print("------------------------------------------------------------")
print(resc_string)

with open("uploads/example.repl", "w") as f:
    f.write(repl_string)

with open("uploads/example.resc", "w") as f:
    f.write(resc_string)

def remove_duplicates(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Tekrarlayanları kaldır (satır sırasını koruyarak)
    seen = set()
    unique_lines = []
    for line in lines:
        if "include" not in line:
            unique_lines.append(line)
            continue
        if line not in seen:
            unique_lines.append(line)
            seen.add(line)

    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(unique_lines)


remove_duplicates("uploads/example.repl")
remove_duplicates("uploads/example.resc")

from graphviz import Digraph


def create_diagram(data):

    dot = Digraph(
        comment=f"{data['mcu']} Connections",
        format="png"
    )

    dot.attr(
        rankdir="LR",
        bgcolor="white",
        splines="spline",
        nodesep="0.8",
        ranksep="1.2"
    )

    # ---------------------------------------------------
    # MCU
    # ---------------------------------------------------

    dot.node(
        "MCU",
        f"<<B>{data['mcu']}</B>>",
        shape="box3d",
        style="filled,bold",
        fillcolor="#4F8EF7",
        fontcolor="white",
        fontsize="22"
    )

    # ---------------------------------------------------
    # Connection list
    # ---------------------------------------------------

    for idx, conn in enumerate(data["connections"]):

        peripheral = conn["peripheral"]
        sensor = conn["sensor"]

        periph_node = f"PERIPH_{idx}"
        sensor_node = f"SENSOR_{idx}"

        # ---------------------------------
        # Peripheral label
        # ---------------------------------

        peripheral_label = peripheral

        if (
            peripheral.upper() == "GPIO"
            and conn.get("port")
            and conn.get("pin")
        ):
            peripheral_label = (
                f"{peripheral}\\n"
                f"({conn['port']}{conn['pin']})"
            )

        elif (
            "I2C" in peripheral.upper()
            and conn.get("slaveId")
        ):
            peripheral_label = (
                f"{peripheral}\\n"
                f"(Slave {conn['slaveId']})"
            )

        # ---------------------------------
        # Peripheral color
        # ---------------------------------

        color_map = {
            "GPIO": "#FFE699",
            "I2C": "#BDD7EE",
            "SPI": "#C6E0B4",
            "USART": "#F8CBAD",
            "UART": "#F8CBAD",
            "CAN": "#D9D2E9",
            "ADC": "#F4CCCC",
            "PWM": "#FFD966"
        }

        color = "#EDEDED"

        for key, value in color_map.items():
            if key in peripheral.upper():
                color = value
                break

        # ---------------------------------
        # Peripheral node
        # ---------------------------------

        dot.node(
            periph_node,
            peripheral_label,
            shape="box",
            style="rounded,filled",
            fillcolor=color,
            fontsize="12"
        )

        # ---------------------------------
        # Sensor node
        # ---------------------------------

        dot.node(
            sensor_node,
            sensor,
            shape="ellipse",
            style="filled",
            fillcolor="white",
            color=color,
            penwidth="2",
            fontsize="12"
        )

        # ---------------------------------
        # Connections
        # ---------------------------------

        dot.edge(
            "MCU",
            periph_node,
            color="#555555",
            penwidth="2"
        )

        dot.edge(
            periph_node,
            sensor_node,
            color="#888888",
            penwidth="2"
        )

    # ---------------------------------------------------
    # Legend
    # ---------------------------------------------------

    with dot.subgraph(name="cluster_legend") as c:

        c.attr(
            label="Legend",
            fontsize="12"
        )

        c.node(
            "L1",
            "GPIO",
            shape="box",
            style="filled",
            fillcolor="#FFE699"
        )

        c.node(
            "L2",
            "I2C",
            shape="box",
            style="filled",
            fillcolor="#BDD7EE"
        )

        c.node(
            "L3",
            "SPI",
            shape="box",
            style="filled",
            fillcolor="#C6E0B4"
        )

        c.node(
            "L4",
            "USART",
            shape="box",
            style="filled",
            fillcolor="#F8CBAD"
        )

        c.node(
            "L5",
            "CAN",
            shape="box",
            style="filled",
            fillcolor="#F4CCCC"
        )

    output_path = "uploads/diagram"

    dot.render(
        output_path,
        # cleanup=True,
        view=False
    )

    print(
        f"diagram created: {output_path}.png"
    )


create_diagram(data)
