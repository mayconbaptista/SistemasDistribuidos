#!/bin/bash

# Verifica se o número de argumentos é correto
if [ "$#" -ne 3 ]; then
    echo "Uso: $0 porta client arquivo_teste"
    exit 1
fi

# Nome do arquivo fornecido como argumento
arquivo="$3"
port="$2"
client="$1"

# Verifica se o arquivo existe
if [ ! -f "$arquivo" ]; then
    echo "Erro: O arquivo '$arquivo' não existe."
    exit 1
fi

while read -r linha; do

    # echo "$port:$linha"

    python3 "$client $port $linha"

done < "$arquivo"
