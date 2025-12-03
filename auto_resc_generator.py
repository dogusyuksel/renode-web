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

resc_string += """
using sysbus
mach create
machine LoadPlatformDescription @/workspace/uploads/example.repl
sysbus LoadELF @/workspace/uploads/firmware.elf
sysbus.cpu LogFunctionNames true
"""

button_substring = ""
counter = 0
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
            repl_string += f'{item["sensor"]}: Antmicro.Renode.Peripherals.I2C.{item["sensor"]} @ {item["peripheral"].lower()} 0xAA\n'
        else:
            repl_string += f'{item["sensor"]}: I2C.{item["sensor"]} @ {item["peripheral"].lower()} 0xAA\n'
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


resc_string += """
emulation RunFor "10s"
start
"""

if it_has_button:
    resc_string += button_substring + "\n"

resc_string += """
quit
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

    # Aynı dosyaya tekrar yaz
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(unique_lines)


remove_duplicates("uploads/example.repl")
remove_duplicates("uploads/example.resc")

from graphviz import Digraph

def create_diagram(data):
    dot = Digraph(comment=f"{data['mcu']} Connections", format="png")
    dot.attr(rankdir="LR", bgcolor="#f8f9fa", splines="ortho")

    # MCU ortada, daha büyük
    dot.node("MCU", data["mcu"], shape="box3d", style="filled,bold", fillcolor="#91c9ff", fontsize="18")

    for conn in data["connections"]:
        sensor_label = conn["sensor"]
        peripheral = conn["peripheral"]

        # GPIO ise port/pin bilgisi ekle
        if peripheral == "GPIO":
            sensor_label += f"\\n{conn['port']}:{conn['pin']}"

        # Renk kodu belirle
        color_map = {
            "GPIO": "#fff3b0",
            "I2C": "#bde0fe",
            "SPI": "#b9fbc0",
            "USART": "#ffd6a5",
            "CAN": "#caffbf",
            "ADC": "#ffc6ff"
        }
        color = "#e2e2e2"
        for key, c in color_map.items():
            if key in peripheral.upper():
                color = c
                break

        # Düğüm oluştur
        dot.node(sensor_label, sensor_label, shape="ellipse", style="filled", fillcolor=color, fontsize="12")

        # Kenar etiketini net göster
        dot.edge("MCU", sensor_label, label=peripheral, fontsize="10", fontcolor="#555555")

    output_path = "uploads/diagram"
    dot.render(output_path, view=False)
    print(f"diagram created: {output_path}.png")


create_diagram(data)
