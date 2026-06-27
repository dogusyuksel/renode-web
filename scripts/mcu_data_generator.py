import os
import json


MCU_DIR = "/workspace/extendedcpus"
PERIPH_DIR = "/workspace/peripherals"
OUTPUT_FILE = "/workspace/web/static/mcu_data.json"


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

    with open(f"{MCU_DIR}/{file}", "r") as f:
        for line in f:
            words = line.strip().split(" ")
            if len(words) < 2:
                continue
            if words[0][-1] != ":":
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
    if not os.path.exists(path):
        return []
    namelist = [
        os.path.splitext(f)[0]
        for f in os.listdir(path)
        if (os.path.isfile(os.path.join(path, f)) and not f.startswith("."))
    ]

    return namelist


def build_json_structure(
    result,
    mcu_name,
    ports,
    pins,
    i2c_list,
    spi_list,
    adc_list,
    gpio_list,
    can_list,
    uart_list,
    usart_list,
):
    mcu_name_fixed = mcu_name.split(".", 1)[0]

    peripherals = {}

    for i2c in i2c_list:
        sensors = list_files_no_ext(os.path.join(PERIPH_DIR, "i2c"))
        if sensors:
            peripherals[i2c] = sensors

    for spi in spi_list:
        sensors = list_files_no_ext(os.path.join(PERIPH_DIR, "spi"))
        if sensors:
            peripherals[spi] = sensors

    for gpio in gpio_list:
        devices = list_files_no_ext(os.path.join(PERIPH_DIR, "gpio"))
        if devices:
            peripherals[gpio] = devices

    for adc in adc_list:
        devices = list_files_no_ext(os.path.join(PERIPH_DIR, "adc"))
        if devices:
            peripherals[adc] = devices

    for can in can_list:
        devices = list_files_no_ext(os.path.join(PERIPH_DIR, "can"))
        if devices:
            peripherals[can] = devices

    for uart in uart_list:
        devices = list_files_no_ext(os.path.join(PERIPH_DIR, "uart"))
        if devices:
            peripherals[uart] = devices

    for usart in usart_list:
        devices = list_files_no_ext(os.path.join(PERIPH_DIR, "usart"))
        if devices:
            peripherals[usart] = devices

    result[mcu_name_fixed] = {"ports": ports, "pins": pins, "peripherals": peripherals}

    return result


if __name__ == "__main__":
    result = {}

    files = os.listdir(f"{MCU_DIR}")
    for file in files:
        if not file.endswith(".repl"):
            continue

        perips = parse_perips(file)
        # print(perips)

        ports = perips["gpio"]
        pins = list(range(32))
        i2c = perips["i2c"]
        spi = perips["spi"]
        adc_list = ["adc"]
        gpio_list = ["gpio"]
        can_list = ["can"]
        uart = perips["uart"]
        usart = perips["usart"]

        build_json_structure(
            result,
            file,
            ports,
            pins,
            i2c,
            spi,
            adc_list,
            gpio_list,
            can_list,
            uart,
            usart,
        )

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)
