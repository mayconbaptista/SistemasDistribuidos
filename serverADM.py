#!.venv/bin/python3
from concurrent import futures
import logging
import grpc
import portalADM_pb2 
import portalADM_pb2_grpc
import paho.mqtt.client as mqtt
import sys
import socket
import json
from data import *

############################################## Variaveis globais #####################################

# Configurações do servidor
HOST = '127.0.0.1'
PORT = 12345

# Configurações do broker MQTT
MQTT_BROKER_HOST = '127.0.0.1' # 'mqtt.eclipseprojects.io'
MQTT_BROKER_PORT = 1883
MQTT_TOPIC_BASE = 'portal/'

dados_alunos      = dict()
dados_professores = dict()
dados_disciplinas = dict()

STATUS_OK    = 0
STATUS_ERROR = 1

###################################### Funções do da conecção do mqtt ###########################

# Função para lidar com a conexão MQTT
def on_connect(client, userdata, flags, reason_code, properties):

    if reason_code.is_failure:
        print(f"Falha ao conectar: ​​{reason_code}. loop_forever() tentará novamente a conexão")
        sys.exit(1)
    else:
        # assinamdo o retorno de chamada on_connect para ter certeza
        # nossa assinatura persiste nas reconexões.
        # subescrevendo em toda a arvore de tópicos até a raiz portal
        client.subscribe(MQTT_TOPIC_BASE + "#")

# Função para lidar com mensagens recebidas do broker MQTT
def on_message(client, userdata, msg):

    print(f"Mensagem recebida do tópico -> {msg.topic}: {msg.payload.decode()}")

# Configuração do cliente MQTT
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

############################### Classes com as funções chamadas via RPC #########################

# classe portalAdministrativo que conterá as funções clamadas via RPC
class PortalAdministrativo (portalADM_pb2_grpc.PortalAdministrativoServicer):

    # Método para manipular a solicitação GetUsers
    def NovoAluno(self, request, context): #ok
        try:
            if(not dados_alunos.get(request.matricula)):               
                dados_alunos[request.matricula] = Aluno(matricula=request.matricula,nome=request.nome) 
                mqtt_client.publish(MQTT_TOPIC_BASE + "aluno", f"--op create --base aluno --key {request.matricula} --val {request.nome}", 0 )
                return portalADM_pb2.Status(status=STATUS_OK, msg=f"Created")
            else:
                return portalADM_pb2.Status(status=STATUS_ERROR, msg=f"Conflict key:{request.matricula}")
        
        except Exception as e:
            return portalADM_pb2.Status(status=STATUS_ERROR, msg=f"Bad_request: {str(e)}")
    
    def EditaAluno(self, request, context): #ok
        try:
            if(dados_alunos.get(request.matricula)):

                dados_alunos[request.matricula] = Aluno(matricula=request.matricula, nome=request.nome)
                mqtt_client.publish( MQTT_TOPIC_BASE + "aluno", f"--op update --base aluno --key {request.matricula} --val {request.nome}", 0 )
                return portalADM_pb2.Status(status=STATUS_OK, msg=f"Ok")
            else:
                return portalADM_pb2.Status(status=STATUS_ERROR, msg=f"Not_found key:{request.matricula}")
            
        except Exception as e:
            return portalADM_pb2.Status(status=STATUS_ERROR, msg=f"Bad_request: {str(e)}")
    
    def RemoveAluno(self, request, context): # ok

        try:
            dados_alunos.pop(request.id)
            mqtt_client.publish( MQTT_TOPIC_BASE + "aluno", f"--op delete --base aluno --key {request.id}", 0 )
            return portalADM_pb2.Status(status=STATUS_OK, msg=f"Aluno {request.id} removido com sucesso!")
        except Exception as e:
            return portalADM_pb2.Status(status=STATUS_ERROR, msg=f"Not_found: {str(e)}")
        
    def ObtemAluno(self, request, context): # ok

        try:
            if(dados_alunos.get(request.id)):
                aluno = dados_alunos.get(request.id)
                return portalADM_pb2.Aluno(matricula=aluno.matricula, nome=aluno.nome)
            else:
                return portalADM_pb2.Aluno(matricula="", nome="")
        except Exception as e:
            return portalADM_pb2.Aluno(matricula="", nome="")

    def ObtemTodosAlunos(self, request, context):
        for aluno in dados_alunos.values():
            yield portalADM_pb2.Aluno(matricula=aluno.matricula, nome=aluno.nome)

    ################################################### professor ####################################################

    def NovoProfessor(self, request, context):
        
        try:
            if(not dados_professores.get(request.siape)): #ok
                dados_professores[request.siape] = Professor(siape=request.siape, nome=request.nome)
                mqtt_client.publish( MQTT_TOPIC_BASE + "professor", f"--op create --base professor --key {request.siape} --val {request.nome}", 0 )
                return portalADM_pb2.Status(status=STATUS_OK, msg="Created")
            else:
                return portalADM_pb2.Status(status=STATUS_ERROR, msg=f"Conflict key:{request.siape}")
        except Exception as e:
            return portalADM_pb2.Status(status=STATUS_ERROR, msg=f"Bad_request: {str(e)}")
        
    def EditaProfessor(self, request, context):
        try:
            if(dados_professores.get(request.siape)):
                dados_professores[request.siape] = Professor(siape=request.siape, nome=request.nome)
                mqtt_client.publish( MQTT_TOPIC_BASE + "professor", f"--op update --base professor --key {request.siape} --val {request.nome}", 0 )
                return portalADM_pb2.Status(status=STATUS_OK, msg="Ok")
            else:
                return portalADM_pb2.Status(status=STATUS_ERROR, msg=f"Not_found: key:{request.siape}")
        except Exception as e:
            return portalADM_pb2.Status(status=STATUS_ERROR, msg=f"Bad_Request: {str(e)}")
        
    def RemoveProfessor(self, request, context):
        try:
            dados_professores.pop(request.id)
            mqtt_client.publish( MQTT_TOPIC_BASE + "professor", f"--op remove --base professor --key {request.id}", 0 )
            return portalADM_pb2.Staus(status=STATUS_OK, msg="ok")
        
        except KeyError as e:
            return portalADM_pb2.Status(status=STATUS_ERROR, msg=f"Not_found key:{id}")
        
    def ObtemProfessor(self, request, context):
        
        try:
            if(dados_professores.get(request.id)):
                professor = dados_professores.get(request.id)
                return portalADM_pb2.Professor(siape=professor.siape, nome=professor.nome)

            else:
                return portalADM_pb2.Professor(siape=" ", nome=" ")
        except Exception as e:
            return portalADM_pb2.Professor(siape="", nome="")
        
    def ObtemTodosProfessores(self, request, context):
        
        for professor in dados_professores.values():
            yield portalADM_pb2.Professor(matricula=professor.siape, nome=professor.nome)

    ###################################################### disciplina #################################################

    def NovaDisciplina(self, request, context):

        try:
            if(not dados_disciplinas.get(request.sigla)):
                dados_disciplinas[request.sigla] = Disciplina(sigla=request.sigla, nome=request.nome, vagas=request.vagas)
                mqtt_client.publish( MQTT_TOPIC_BASE + "disciplina", f"--op create --base disciplina --key {request.sigla} --val {request.nome} {request.vagas}", 0 )
                return portalADM_pb2.Status(status=STATUS_OK, msg="Created")
            else:
                return portalADM_pb2.Status(status=STATUS_ERROR, msg="Conflict")

        except Exception as e:
            return portalADM_pb2.Status(status=STATUS_ERROR, msg=f"Bad_request {str(e)}") 
        
    def EditaDisciplina(self, request, context):
        try:
            if(dados_disciplinas.get(request.sigla)):
            
                dados_disciplinas[request.sigla] = Disciplina(sigla=request.sigla, nome=request.nome, vagas=request.vagas)
                mqtt_client.publish( MQTT_TOPIC_BASE + "disciplina", f"--op update --base disciplina --key {request.sigla} --val {request.nome} {request.vagas}", 0 )
                return portalADM_pb2.Status(status=STATUS_OK, msg="Ok")
            else:
                return portalADM_pb2.Status(status=STATUS_ERROR, msg=f"Not_found: key:{request.sigla}")
        except Exception as e:
            return portalADM_pb2.Status(status=STATUS_ERROR, msg=f"Bad_request {str(e)}")
        
    def RemoveDisciplina(self, request, context):
        
        try:
            dados_disciplinas.pop(request.id)
            mqtt_client.publish( MQTT_TOPIC_BASE + "disciplina", f"--op delete --base disciplina --key {request.id}", 0 )
            return portalADM_pb2.Status(status=STATUS_OK, msg="ok")
        
        except KeyError as e:
            return portalADM_pb2.Status(status=STATUS_ERROR, msg="Not found")
        
    def ObtemDisciplina(self, request, context):
        try:
            if(dados_disciplinas.get(request.id)):

                disciplina = dados_disciplinas.get(request.id)
                return portalADM_pb2.Disciplina(sigla=disciplina.sigla, nome=disciplina.nome, vagas=disciplina.vagas)

            else:
                return portalADM_pb2.Disciplina(sigla=" ", nome=" ", vagas=0)
        except Exception as e:
            return portalADM_pb2. Disciplina(sigla="", nome="", vagas=0)
        
    def ObtemTodasDisciplinas(self, request, context):
        
        for disciplina in dados_disciplinas.values():
            yield portalADM_pb2.Disciplina(sigla=disciplina.sigla, nome=disciplina.nome, vagas=disciplina.vagas)


# Função para iniciar o servidor gRPC
def serve():

    # try:

    # Criação do servidor gRPC com um pool de threads
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Registro do serviço PortalAdmistrativo na instância do servidor
    portalADM_pb2_grpc.add_PortalAdministrativoServicer_to_server(PortalAdministrativo(), server)

    # Conecta-se ao broker MQTT
    mqtt_client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
    mqtt_client.loop_start()

    # Adiciona uma porta de escuta não segura (insecure) no servidor
    server.add_insecure_port('[::]:50051')

    # Inicia o servidor
    server.start()

    #except KeyboardInterrupt:
    #    print("\nPrograma interrompido pelo usuário. Encerrando...")

    # Aguarda a finalização do servidor
    server.wait_for_termination()

    # Desconecta do broker MQTT ao encerrar o servidor
    mqtt_client.loop_stop()
    mqtt_client.disconnect()


if __name__ == '__main__':
    # Configuração do logging básico
    logging.basicConfig()
    print("Iniciando servidor em: %s" % ('localhost:50051'))

    # Inicia o servidor
    serve()