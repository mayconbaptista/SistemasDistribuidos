# SistemasDistribuidos

Projetos feitos na disciplina de sistemas distribuídos do cursos de Ciências da Computação ufu.
Esse projetos consiste em um sistema distribuido utilizando o framework [grpc]().

O projeto consiste em implementar um Sistema de Matrícula com armazenamento chave-valor (key-value store = KVS).

A arquitetura do sistema será híbrida, contendo um pouco de cliente/servidor, publish/subscribe e Peer-2-Peer, além de ser multicamadas. Apesar de introduzir complexidade extra, também usaremos múltiplos mecanismos para a comunicação entre as partes, para que possam experimentar com diversas abordagens.

### Integrantes
* Maycon douglas bartista dos santos
* Carlos Antonio
* Carlos Junior

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