#!/bin/bash

python3 -m pip install virtualenv # instalando o virtualenv

virtualenv .venv # criando um ambiente virtual

source .venv/bin/activate # ativando o ambiente virtual

python3 -m pip install --upgrade pip

git clone -b v1.60.1 --depth 1 --shallow-submodules https://github.com/grpc/grpc # clonando o projeto grpc

python3 -m pip install -r requirements.txt

# Isso regenera _pb2.py o que contém nossas classes de solicitação e resposta geradas
python3 -m grpc_tools.protoc -I./proto --python_out=. --grpc_python_out=. ./proto/portalADM.proto

# já _pb2_grpc.py que contém nossas classes de cliente e servidor geradas.
python3 -m grpc_tools.protoc -I./proto --python_out=. --grpc_python_out=. ./proto/portalMat.proto 
