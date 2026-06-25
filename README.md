# renode-web

This project is used for creating renode resc and repl with a web UI easily!

<img src="./images/renode-web.png" />



## HOW TO

First, setup environment. Please note that, this project assumes your project path is at "/workspace", or use Docker!


```
./setup_env.sh

```

execute web applicaion

```
python app.py # under web folder
```

and open browser and type the url you saw on logs
then follow the instructions and check the console


## LIMITATIONS

* only single sensor can be connected to each peripheral


## TODO

* Pass test duration and function logging property from web to system


## NOTES

function logging enable

```
sysbus LoadELF @/workspace/uploads/firmware.elf
sysbus.cpu LogFunctionNames true
```
