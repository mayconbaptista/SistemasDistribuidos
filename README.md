# SistemasDistribuidos

Projetos feitos na disciplina de sistemas distribuídos do cursos de Ciências da Computação ufu.
Esse projetos consiste em um sistema distribuido utilizando o framework [grpc]().

O projeto consiste em implementar um Sistema de Matrícula com armazenamento chave-valor (key-value store = KVS).

A arquitetura do sistema será híbrida, contendo um pouco de cliente/servidor, publish/subscribe e Peer-2-Peer, além de ser multicamadas. Apesar de introduzir complexidade extra, também usaremos múltiplos mecanismos para a comunicação entre as partes, para que possam experimentar com diversas abordagens.

### Integrantes
* Maycon douglas bartista dos santos
* Carlos Antonio
* Carlos Junior

Video: https://www.youtube.com/watch?v=tAX-8CN_Ms8

## Como executar?

todos os comando para execução estão no arguivo compile.sh

## comunicação entre servidores

A comunicação entre servidores seque a arquitetura p2p onde é usada o protodocolo de comunicação MQTT implementado atravez do mosquitto.

Os tópicos de publicação no broker sequem a arquitetura rest, o servidor administrativo publica nos sequintes tópicos:

* portal/admin/aluno/create
* portal/admin/aluno/update
* portal/admin/aluno/delete

* portal/admin/professor/create
* portal/admin/professor/update
* portal/admin/professor/delete

* portal/admin/disciplina/create
* portal/admin/disciplina/update
* portal/admin/disciplina/delete

Pode se acompanhar todas as publucações no broker com o sequinte comando: mosquitto_sub -t portal/# -v

Para testar a comunicação podem ser publicados nos tópicos manualmente usando o mosquitto ex:

* mosquitto_pub -t portal/aluno -m "teste connect"
* mosquitto_pub -t portal/admin/aluno/create -m "11921BSI209,maycon"
* mosquitto_pub -t portal/admin/aluno/update -m "11921BSI209,maycon edit"
* mosquitto_pub -t portal/admin/aluno/update -m "11921BSI201,errornot found edit"
* mosquitto_pub -t portal/admin/aluno/delete -m "11921BSI201"
* mosquitto_pub -t portal/admin//delete -m "11921BSI209"
* mosquitto_pub -t portal/admin/professor/create -m "1524,pedro"
* mosquitto_pub -t portal/admin/professor/create -m "1525,Miane"
* mosquitto_pub -t portal/admin/professor/update -m "1525,Miane edit"
* mosquitto_pub -t portal/admin/professor/delete -m "1525"
* mosquitto_pub -t portal/admin/disciplina/create -m "BSI034,prolog,30"
* mosquitto_pub -t portal/admin/disciplina/update -m "BSI035,prolog,30"
* mosquitto_pub -t portal/admin/disciplina/update -m "BSI034,prolog edit,29"
* mosquitto_pub -t portal/admin/disciplina/delete -m "BSI035"
* mosquitto_pub -t portal/admin/disciplina/delete -m "BSI034"

O serverADM irá sincronizar seu banco de dados com base nas atualizações publicadas.

Etapa 2:

Iniciando os bancos:
*python3 kvstorage.py localhost:5000 db1 8001 localhost:5001 localhost:5002
*python3 kvstorage.py localhost:5001 db2 8002 localhost:5000 localhost:5002
*python3 kvstorage.py localhost:5002 db3 8003 localhost:5000 localhost:5001
