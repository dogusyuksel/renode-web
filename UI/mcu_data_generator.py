import os
import json


# ====== Klasör kökleri ======
MCU_DIR = "../extendedcpus"
PERIPH_DIR = "../peripherals"
OUTPUT_FILE = "mcu_data.json"

def parse_perips(file):
    print(f"Parsing peripherals from {file}")

    result = {
        "gpio": [],
        "i2c": [],
        "spi": [],
        "uart": [],
        "usart": [],
        "gpio": [],
    }

    with open(f"../extendedcpus/{file}", "r") as f:
        for line in f:
            words = line.strip().split(" ")
            if len(words) < 2:
                continue
            if words[0][-1] != ':':
                continue
            key = words[0][:-1]
            if "gpio" in key:
                result["gpio"].append(key)

            if "i2c" in key:
                result["i2c"].append(key)

            if "spi" in key:
                result["spi"].append(key)

            if "uart" in key:
                result["uart"].append(key)

            if "usart" in key:
                result["usart"].append(key)

    if os.path.exists(f"../cpus/{file}"):
        with open(f"../cpus/{file}", "r") as f:
            for line in f:
                words = line.strip().split(" ")
                if len(words) < 2:
                    continue
                if words[0][-1] != ':':
                    continue
                key = words[0][:-1]
                if "gpio" in key:
                    result["gpio"].append(key)

                if "i2c" in key:
                    result["i2c"].append(key)

                if "spi" in key:
                    result["spi"].append(key)

                if "uart" in key:
                    result["uart"].append(key)

                if "usart" in key:
                    result["usart"].append(key)

    return result

def list_files_no_ext(path):
    """Klasördeki gizli olmayan dosya isimlerini (uzantısız) döndürür"""
    if not os.path.exists(path):
        return []
    namelist = [
        os.path.splitext(f)[0]
        for f in os.listdir(path)
        if (
            os.path.isfile(os.path.join(path, f))
            and not f.startswith('.')        # gizli dosyaları hariç tut
        )
    ]
    
    return namelist

def build_json_structure(result, mcu_name, ports, pins, i2c_list, spi_list, adc_list, gpio_list, can_list, uart_list, usart_list):
    mcu_name_fixed = mcu_name.split('.', 1)[0]

    peripherals = {}

    # I2C cihazlarını eşleştir
    for i2c in i2c_list:
        sensors = list_files_no_ext(os.path.join(PERIPH_DIR, "i2c"))
        if sensors:
            peripherals[i2c] = sensors

    # SPI cihazlarını eşleştir
    for spi in spi_list:
        sensors = list_files_no_ext(os.path.join(PERIPH_DIR, "spi"))
        if sensors:
            peripherals[spi] = sensors

    # GPIO cihazları
    for gpio in gpio_list:
        devices = list_files_no_ext(os.path.join(PERIPH_DIR, "gpio"))
        if devices:
            peripherals[gpio] = devices

    # ADC cihazları
    for adc in adc_list:
        devices = list_files_no_ext(os.path.join(PERIPH_DIR, "adc"))
        if devices:
            peripherals[adc] = devices

    # can cihazları
    for can in can_list:
        devices = list_files_no_ext(os.path.join(PERIPH_DIR, "can"))
        if devices:
            peripherals[can] = devices

    # uart cihazları
    for uart in uart_list:
        devices = list_files_no_ext(os.path.join(PERIPH_DIR, "uart"))
        if devices:
            peripherals[uart] = devices

    # uart cihazları
    for usart in usart_list:
        devices = list_files_no_ext(os.path.join(PERIPH_DIR, "usart"))
        if devices:
            peripherals[usart] = devices

    # MCU verisini oluştur
    result[mcu_name_fixed] = {
        "ports": ports,
        "pins": pins,
        "peripherals": peripherals
    }

    return result


if __name__ == "__main__":
    result = {}

    files = os.listdir("../extendedcpus")
    for file in files:
        if not file.endswith(".repl"):
            continue

        perips = parse_perips(file)
        # print(perips)

        # ====== Elindeki sabit listeler ======
        ports = perips["gpio"]
        pins = list(range(32))
        i2c = perips["i2c"]
        spi = perips["spi"]
        adc_list = ["adc"]
        gpio_list = ["gpio"]
        can_list = ["can"]
        uart = perips["uart"]
        usart = perips["usart"]

        build_json_structure(result, file, ports, pins, i2c, spi, adc_list, gpio_list, can_list, uart, usart)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)
