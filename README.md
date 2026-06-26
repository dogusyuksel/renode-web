# renode-web

This project is used for creating renode resc and repl with a web UI easily!

<img src="./images/renode-web.png" />



## HOW TO

First, setup environment. Please note that, this project assumes your project path is at "/workspace", or use Docker (just execute './docker_ctl -b -s')


```
./setup_env.sh

```

execute web applicaion

```
python app.py # under web folder
```

and open browser and type the url you saw on logs
then follow the instructions and check the console

Pleae note that if web UI is not up-to-date (missing mcu in dropdown etc) then please execute below command first.

```
cd UI
python3 mcu_data_generator.py
```


## LIMITATIONS

* only single sensor can be connected to each peripheral


## EXAMPLE REPORT

[Open the PDF](./images/report.pdf)
