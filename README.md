Introducción a los Sistemas Distribuidos (75.43)

TP N◦2: File Transfer

# Integrantes

- Cai, Ana Maria 102150
- Barreneche, Franco 102205
- Illescas, Geronimo 102071
- Carol Lugones, Ignacio 100073
- Torresetti, Lisandro 99846

## Developer basic commands

Excecute unit tests with pytest

``` bash
make test
```

Excecute reformatting with black to be compliant with pep8

``` bash
make reformat
```

Run basic app

``` bash
make run
```

## User basic commands

### Start Server

``` bash
$ python3 src/start-server.py -h
usage: start-server [ - h ] [ - v | -q ] [ - H ADDR ] [ - p PORT ] [- s DIRPATH ]

Interfaz del servidor

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         verbose increase output verbosity
  -q, --quiet           quiet decrease output verbosity
  -H HOST, --host HOST  server IP address
  -p PORT, --port PORT  server port
  -s STORAGE, --storage STORAGE
                        storage dir path
  -a ARQUITECTURE, --arquitecture ARQUITECTURE
                        arquitecture: select_and_repeat or stop_and_wait
```

### Upload files

``` bash
python3 src/upload.py -h
usage: upload [ - h ] [ - v | -q ] [ - H ADDR ] [ - p PORT ] [ - s FILEPATH ] [ - n FILENAME ]

UPLOAD: Transferencia de un archivo del cliente hacia el servidor.

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         verbose increase output verbosity
  -q, --quiet           quiet decrease output verbosity
  -H HOST, --host HOST  server IP address
  -p PORT, --port PORT  server port
  -s SRC, --src SRC     source file path
  -n NAME, --name NAME  file name
  -a ARQUITECTURE, --arquitecture ARQUITECTURE
                        arquitecture: select_and_repeat or stop_and_wait
```

### Downloaded files

``` bash
python3 src/download.py -h
usage: download [ - h ] [ - v | -q ] [ - H ADDR ] [ - p PORT ] [ - d FILEPATH ] [ - n FILENAME ]

DOWNLOAD: Transferencia de un archivo del servidor hacia el cliente.

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         verbose increase output verbosity
  -q, --quiet           quiet decrease output verbosity
  -H HOST, --host HOST  server IP address
  -p PORT, --port PORT  server port
  -d DST, --dst DST     source file path
  -n NAME, --name NAME  file name
  -a ARQUITECTURE, --arquitecture ARQUITECTURE
                        arquitecture: select_and_repeat or stop_and_wait
```

## Examples

### Stop and wait

Start server example:

``` bash
python3 src/start-server.py -H "localhost" -p 8080 -s "./testr" -a "stop_and_wait"
```

Start upload file example:

``` bash
python3 src/upload.py -H "localhost" -p 8080 -s "./test" -a "stop_and_wait"
```

Start download file example:

``` bash
python3 src/download.py -H "localhost" -p 8080 -d "./test" -a "stop_and_wait"
```

### Select and repeat

Start server example:

``` bash
python3 src/start-server.py -H "localhost" -p 8080 -s "./test" -a "select_and_repeat"
```

Start upload file example:

``` bash
python3 src/upload.py -H "localhost" -p 8080 -s "./test" -a "select_and_repeat"
```

Start download file example:

``` bash
python3 src/download.py -H "localhost" -p 8080 -d "./test" -a "select_and_repeat"
