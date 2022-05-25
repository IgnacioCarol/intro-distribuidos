# Introducción a los Sistemas Distribuidos (75.43)
# TP N◦2: File Transfer

## Integrantes



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
$  python3 start-server.py -h
usage: start-server [ - h ] [ - v | -q ] [ - H ADDR ] [ - p PORT ] [- s DIRPATH ]

Interfaz del servidor

optional arguments:
  -h, --help            show this help message and exit
  -v VERBOSE, --verbose VERBOSE
                        verbose increase output verbosity
  -q QUIT, --quit QUIT  quiet decrease output verbosity
  -H HOST, --host HOST  server IP address
  -p PORT, --port PORT  server port
  -s STORAGE, --storage STORAGE
                        storage dir path
```

``` bash
$ python3 start-server.py -H "localhost" -p 8080 -s "./test"
```

### Upload files

``` bash

$ python3 upload.py -h
usage: upload [ - h ] [ - v | -q ] [ - H ADDR ] [ - p PORT ] [ - s FILEPATH ] [ - n FILENAME ]

UPLOAD: Transferencia de un archivo del cliente hacia el servidor.

optional arguments:
  -h, --help            show this help message and exit
  -v VERBOSE, --verbose VERBOSE
                        verbose increase output verbosity
  -q QUIT, --quit QUIT  quiet decrease output verbosity
  -H HOST, --host HOST  server IP address
  -p PORT, --port PORT  server port
  -s SRC, --src SRC     source file path
```

``` bash
$ python3 upload.py -H "0.0.0.0" -p 8080 -n "lorem_ipsum.txt"
```

### Downloaded files

``` bash
$ python3 download.py -h

usage: download [ - h ] [ - v | -q ] [ - H ADDR ] [ - p PORT ] [ - d FILEPATH ] [ - n FILENAME ]

DOWNLOAD: Transferencia de un archivo del servidor hacia el cliente.

optional arguments:
  -h, --help            show this help message and exit
  -v VERBOSE, --verbose VERBOSE
                        verbose increase output verbosity
  -q QUIT, --quit QUIT  quiet decrease output verbosity
  -H HOST, --host HOST  server IP address
  -p PORT, --port PORT  server port
  -d DST, --dst DST     source file path
  -n NAME, --name NAME  file name
```

``` bash
$ python3 download.py -H "localhost" -p 8080 -d "./test" -n "lorem_ipsum_copy.txt"
```
