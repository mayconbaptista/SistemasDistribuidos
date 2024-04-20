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
PORT= int(input("Host: "))
PORTSCKT= int(input("Socket Host: "))

# Configurações do broker MQTT
MQTT_BROKER_HOST = '127.0.0.1' # 'mqtt.eclipseprojects.io'
MQTT_BROKER_PORT = 1883
MQTT_TOPIC_BASE  = 'portal/admin/'

dados_alunos      = dict()
dados_professores = dict()
dados_disciplinas = dict()

STATUS_OK    = 0
STATUS_ERROR = 1
####################################### funções de sincronização de dados entre servidores ######################

def MQTT_sincronize_aluno (event, request):

    try:
        if(str(event).endswith("create")):

            if(not dados_alunos.get(request.get("matricula"))):

                dados_alunos[request.get("matricula")] = json.dumps(request) 

        elif(str(event).endswith("update")):

            if(dados_alunos.get(request.get("matricula"))):

                dados_alunos[request.get("matricula")] = json.dumps(request)

        elif(str(event).endswith("delete")):

            dados_alunos.pop(request.get("matricula"))

    except Exception as e:
        print(f"Sincronize Error: {str(e)}")
        

def MQTT_sincronize_professor (event, request):
    try:
        if(str(event).endswith("create")):

            if(not dados_professores.get(request.get("siape"))):

                dados_professores[request.get("siape")] = json.dumps(request)

        elif(str(event).endswith("update")):

            if(dados_professores.get(request.get("siape"))):

                dados_professores[request.get("siape")] = json.dumps(request)

        elif(str(event).endswith("delete")):

            dados_professores.pop(request.get("siape"))

    except Exception as e:
        print(f"Sincronize Error: {str(e)}")
        

def MQTT_sincronize_disciplina (event, request):
    try:
        if(str(event).endswith("create")):

            if(not dados_disciplinas.get(request.get("sigla"))):

                dados_disciplinas[request.get("sigla")] = json.dumps(request)

        elif(str(event).endswith("update")):

            if(dados_disciplinas.get(request.get("sigla"))):

                dados_disciplinas[request.get("sigla")] = json.dumps(request)

        elif(str(event).endswith("delete")):
            dados_disciplinas.pop(request.get("sigla"))
    except Exception as e:
        print(f"Sincronize Error: {str(e)}")

###################################### Funções do da conecção do mqtt ############################################

# Função para lidar com a conexão MQTT
def on_connect(client, userdata, flags, reason_code, properties):

    if reason_code.is_failure:
        print(f"Falha ao conectar: {reason_code}. loop_forever() tentará novamente a conexão")
        sys.exit(1)
    else:
        # assinamdo o retorno de chamada on_connect para ter certeza
        # nossa assinatura persiste nas reconexões.
        # subescrevendo em toda a arvore de tópicos até a raiz portal/admin
        client.subscribe(MQTT_TOPIC_BASE + "#")

# Função para lidar com mensagens recebidas do broker MQTT
def on_message(client, userdata, msg):

    print(f"Mensagem recebida do tópico -> {msg.topic}: {msg.payload.decode()}")

    payload = json.loads(msg.payload.decode())

    if(str(msg.topic).find("aluno") > -1):
        MQTT_sincronize_aluno(msg.topic, payload)
    elif(str(msg.topic).find("professor") > -1):
        MQTT_sincronize_professor(msg.topic, payload)
    elif(str(msg.topic).find("disciplina") > -1):
        MQTT_sincronize_disciplina(msg.topic, payload)

# Configuração do cliente MQTT
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

######################################### Classes com as funções chamadas via RPC #####################################

def valida(request):

    if type(request) == type(portalADM_pb2.Aluno()):

        if(len(request.matricula) <= 4 or len(request.nome) <= 4):
            raise ValueError("Os campos matricula e nome devem mais de 4 caractares")
        
    elif type(request) == type(portalADM_pb2.Professor()):
        if(len(request.siape) <= 4 or len(request.nome) <= 4):
            raise ValueError("Os campos siape e nome devem ter mais de 4 caracteres")
        
    elif type(request) == type(portalADM_pb2.Disciplina()):
        if(len(request.sigla) <= 4 or len(request.nome) <= 4 or request.vagas <= 0):
            raise ValueError("Os campos sigla e nome devem ter mais de 4 caracteres e numero de vagas não pode iniciar com 0")

# classe portalAdministrativo que conterá as funções clamadas via RPC
class PortalAdministrativo (portalADM_pb2_grpc.PortalAdministrativoServicer):

    # Método para manipular a solicitação GetUsers
    def NovoAluno(self, request, context): #ok
        try:
            if(not dados_alunos.get(request.matricula)):

                valida(request)              

                dados_json = json.dumps({"matricula":request.matricula, "nome":request.nome})

                dados_alunos[request.matricula] = dados_json

                mqtt_client.publish(MQTT_TOPIC_BASE + "aluno/create", dados_json, 0)
                            # Send 'setaluno' command to the other server via socket
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.connect((HOST, PORTSCKT))
                        command = json.dumps({"action": "setaluno", "matricula": request.matricula, "nome": request.nome})
                        sock.sendall(command.encode('utf-8'))
                except Exception as e:
                    print(f"Error sending 'setaluno' command via socket: {str(e)}")
                return portalADM_pb2.Status(status=STATUS_OK, msg=f"Created")
            else:
                return portalADM_pb2.Status(status=STATUS_ERROR, msg=f"Conflict key:{request.matricula}")
        
        except Exception as e:
            return portalADM_pb2.Status(status=STATUS_ERROR, msg=f"Bad_request: {str(e)}")
    
    def EditaAluno(self, request, context): #ok
        try:
            if(dados_alunos.get(request.matricula)):

                valida(request)

                dados_json = json.dumps({"matricula":request.matricula, "nome":request.nome})

                dados_alunos[request.matricula] = dados_json

                mqtt_client.publish( MQTT_TOPIC_BASE + "aluno/update", dados_json, 0 )
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.connect((HOST, PORTSCKT))
                        command = json.dumps({"action": "setaluno", "matricula": request.matricula, "nome": request.nome})
                        sock.sendall(command.encode('utf-8'))
                except Exception as e:
                    print(f"Error sending 'setaluno' command via socket: {str(e)}")
                return portalADM_pb2.Status(status=STATUS_OK, msg=f"Ok")
            else:
                return portalADM_pb2.Status(status=STATUS_ERROR, msg=f"Not_found key:{request.matricula}")
            
        except Exception as e:
            return portalADM_pb2.Status(status=STATUS_ERROR, msg=f"Bad_request: {str(e)}")
    
    def RemoveAluno(self, request, context): # ok

        try:
            dados_alunos.pop(request.id)
            mqtt_client.publish( MQTT_TOPIC_BASE + "aluno/delete",json.dumps({"matricula":request.id}), 0)
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.connect((HOST, PORTSCKT))
                    command = json.dumps({"action": "popaluno", "matricula": request.id})
                    sock.sendall(command.encode('utf-8'))
            except Exception as e:
                print(f"Error sending 'removealuno' command via socket: {str(e)}")
            return portalADM_pb2.Status(status=STATUS_OK, msg="Ok")
        except Exception as e:
            return portalADM_pb2.Status(status=STATUS_ERROR, msg=f"Not_found: {str(e)}")
        
    def ObtemAluno(self, request, context): # ok

        try:
            if(dados_alunos.get(request.id)):
                
                aluno = json.loads(dados_alunos.get(request.id))

                return portalADM_pb2.Aluno(matricula=aluno.get("matricula"), nome=aluno.get("nome"))
            else:
                return portalADM_pb2.Aluno(matricula="", nome="")
        except Exception as e:
            return portalADM_pb2.Aluno(matricula="", nome="")

    def ObtemTodosAlunos(self, request, context):

        for json_aluno in dados_alunos.values():

            aluno = json.loads(json_aluno)

            yield portalADM_pb2.Aluno(matricula=aluno.get("matricula"), nome=aluno.get("nome"))

    ################################################### professor ####################################################

    def NovoProfessor(self, request, context):
        
        try:
            if(not dados_professores.get(request.siape)): #ok

                valida(request)

                professor_json = json.dumps({"siape":request.siape, "nome":request.nome})

                dados_professores[request.siape] = professor_json

                mqtt_client.publish( MQTT_TOPIC_BASE + "professor/create", professor_json, 0 )
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.connect((HOST, PORTSCKT))
                        command = json.dumps({"action": "setprofessor", "siape": request.siape, "nome": request.nome})
                        sock.sendall(command.encode('utf-8'))
                except Exception as e:
                    print(f"Error sending 'setprofessor' command via socket: {str(e)}")
                return portalADM_pb2.Status(status=STATUS_OK, msg="Created")
            else:
                return portalADM_pb2.Status(status=STATUS_ERROR, msg=f"Conflict key:{request.siape}")
        except Exception as e:
            return portalADM_pb2.Status(status=STATUS_ERROR, msg=f"Bad_request: {str(e)}")
        
    def EditaProfessor(self, request, context):
        try:
            if(dados_professores.get(request.siape)):

                valida(request)

                professor_json = json.dumps({"siape":request.siape, "nome":request.nome})

                dados_professores[request.siape] = professor_json

                mqtt_client.publish( MQTT_TOPIC_BASE + "professor/update", professor_json, 0)
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.connect((HOST, PORTSCKT))
                        command = json.dumps({"action": "setprofessor", "siape": request.siape, "nome": request.nome})
                        sock.sendall(command.encode('utf-8'))
                except Exception as e:
                    print(f"Error sending 'setprofessor' command via socket: {str(e)}")

                return portalADM_pb2.Status(status=STATUS_OK, msg="Ok")
            else:
                return portalADM_pb2.Status(status=STATUS_ERROR, msg=f"Not_found: key:{request.siape}")
        except Exception as e:
            return portalADM_pb2.Status(status=STATUS_ERROR, msg=f"Bad_Request: {str(e)}")
        
    def RemoveProfessor(self, request, context):
        try:
            dados_professores.pop(request.id)
            mqtt_client.publish( MQTT_TOPIC_BASE + "professor/delete",json.dumps({"siape":request.id}), 0 )
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.connect((HOST, PORTSCKT))
                    command = json.dumps({"action": "popprofessor", "siape": request.id})
                    sock.sendall(command.encode('utf-8'))
            except Exception as e:
                print(f"Error sending 'removeprofessor' command via socket: {str(e)}")
            return portalADM_pb2.Status(status=STATUS_OK, msg="Ok")
        
        except KeyError as e:
            return portalADM_pb2.Status(status=STATUS_ERROR, msg=f"Not_found key:{request.id}")
        
    def ObtemProfessor(self, request, context):
        
        try:
            if(dados_professores.get(request.id)):

                professor_json = dados_professores.get(request.id)

                professor = json.loads(professor_json)
                return portalADM_pb2.Professor(siape=professor.get("siape"), nome=professor.get("nome"))

            else:
                return portalADM_pb2.Professor(siape=" ", nome=" ")
        except Exception as e:
            return portalADM_pb2.Professor(siape=" ", nome=" ")
        
    def ObtemTodosProfessores(self, request, context):
        
        for professor_json in dados_professores.values():

            professor = json.loads(professor_json)

            yield portalADM_pb2.Professor(siape=professor.get("siape"), nome=professor.get("nome"))

    ###################################################### disciplina #################################################

    def NovaDisciplina(self, request, context):

        try:
            if(not dados_disciplinas.get(request.sigla)):

                valida(request)

                disciplina_json = json.dumps({"sigla":request.sigla, "nome":request.nome, "vagas":request.vagas})

                dados_disciplinas[request.sigla] = disciplina_json

                mqtt_client.publish( MQTT_TOPIC_BASE + "disciplina/create", disciplina_json, 0 )
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.connect((HOST, PORTSCKT))
                        command = json.dumps({"action": "setdisciplina", "sigla": request.sigla, "nome": request.nome, "vagas": request.vagas})
                        sock.sendall(command.encode('utf-8'))
                except Exception as e:
                    print(f"Error sending 'setdisciplina' command via socket: {str(e)}")
                return portalADM_pb2.Status(status=STATUS_OK, msg="Created")
            else:
                return portalADM_pb2.Status(status=STATUS_ERROR, msg=f"Conflict key:{request.sigla}")

        except Exception as e:
            return portalADM_pb2.Status(status=STATUS_ERROR, msg=f"Bad_request {str(e)}") 
        
    def EditaDisciplina(self, request, context):
        try:
            if(dados_disciplinas.get(request.sigla)):

                valida(request)

                disciplina_json = json.dumps({"sigla":request.sigla, "nome":request.nome, "vagas":request.vagas})

                dados_disciplinas[request.sigla] = disciplina_json
            
                mqtt_client.publish( MQTT_TOPIC_BASE + "disciplina/update", disciplina_json, 0)
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.connect((HOST, PORTSCKT))
                        command = json.dumps({"action": "setdisciplina", "sigla": request.sigla, "nome": request.nome, "vagas": request.vagas})
                        sock.sendall(command.encode('utf-8'))
                except Exception as e:
                    print(f"Error sending 'setdisciplina' command via socket: {str(e)}")
                return portalADM_pb2.Status(status=STATUS_OK, msg="Ok")
            else:
                return portalADM_pb2.Status(status=STATUS_ERROR, msg=f"Not_found: key:{request.sigla}")
        except Exception as e:
            return portalADM_pb2.Status(status=STATUS_ERROR, msg=f"Bad_request {str(e)}")
        
    def RemoveDisciplina(self, request, context):
        
        try:
            dados_disciplinas.pop(request.id)
            mqtt_client.publish( MQTT_TOPIC_BASE + "disciplina/delete", json.dumps({"sigla":request.id}), 0)
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.connect((HOST, PORTSCKT))
                    command = json.dumps({"action": "popprofessor", "sigla": request.id})
                    sock.sendall(command.encode('utf-8'))
            except Exception as e:
                print(f"Error sending 'removeprofessor' command via socket: {str(e)}")
            return portalADM_pb2.Status(status=STATUS_OK, msg="ok")
        
        except KeyError as e:
            return portalADM_pb2.Status(status=STATUS_ERROR, msg="Not found")
        
    def ObtemDisciplina(self, request, context):
        try:
            if(dados_disciplinas.get(request.id)):

                disciplina_json = dados_disciplinas.get(request.id)

                disciplina = json.loads(disciplina_json)

                return portalADM_pb2.Disciplina(sigla=disciplina.get("sigla"), nome=disciplina.get("nome"), vagas=disciplina.get("vagas"))

            else:
                return portalADM_pb2.Disciplina(sigla=" ", nome=" ", vagas=0)
        except Exception as e:
            return portalADM_pb2. Disciplina(sigla=" ", nome=" ", vagas=0)
        
    def ObtemTodasDisciplinas(self, request, context):
        
        for disciplina_json in dados_disciplinas.values():

            disciplina = json.loads(disciplina_json)

            yield portalADM_pb2.Disciplina(sigla=disciplina.get("sigla"), nome=disciplina.get("nome"), vagas=disciplina.get("vagas"))


# Função para iniciar o servidor gRPC
def serve():

    # Criação do servidor gRPC com um pool de threads
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Registro do serviço PortalAdmistrativo na instância do servidor
    portalADM_pb2_grpc.add_PortalAdministrativoServicer_to_server(PortalAdministrativo(), server)

    # Conecta-se ao broker MQTT
    mqtt_client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
    mqtt_client.loop_start()

    # Adiciona uma porta de escuta não segura (insecure) no servidor
    server.add_insecure_port(f'[::]:{PORT}')

    # Inicia o servidor
    server.start()

    # Aguarda a finalização do servidor
    server.wait_for_termination()

    # Desconecta do broker MQTT ao encerrar o servidor
    mqtt_client.loop_stop()
    mqtt_client.disconnect()

def get_all_alunos(host, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((host, port))
            command = json.dumps({"action": "getallalunos"})
            sock.sendall(command.encode('utf-8'))
            response = b''
            while True:
                data = sock.recv(1024)
                if not data:
                    break
                response += data
            all_data = json.loads(response.decode('utf-8'))
            for key, value in all_data.items():
                dados_alunos[key] = value
    except Exception as e:
        print(f"Error retrieving all students: {str(e)}")

def get_all_professores(host, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((host, port))
            command = json.dumps({"action": "getallprofessores"})
            sock.sendall(command.encode('utf-8'))
            response = b''
            while True:
                data = sock.recv(1024)
                if not data:
                    break
                response += data
            all_data = json.loads(response.decode('utf-8'))
            for key, value in all_data.items():
                dados_professores[key] = value
    except Exception as e:
        print(f"Error retrieving all professors: {str(e)}")

def get_all_disciplinas(host, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((host, port))
            command = json.dumps({"action": "getalldisciplinas"})
            sock.sendall(command.encode('utf-8'))
            response = b''
            while True:
                data = sock.recv(1024)
                if not data:
                    break
                response += data
            all_data = json.loads(response.decode('utf-8'))
            for key, value in all_data.items():
                dados_disciplinas[key] = value
    except Exception as e:
        print(f"Error retrieving all disciplines: {str(e)}")
 

if __name__ == '__main__':
    # Configuração do logging básico
    logging.basicConfig()
    print("Iniciando servidor em: %s" % (f'localhost:{PORT}'))

    # Inicia o servidor
    get_all_alunos(HOST, PORTSCKT)
    get_all_professores(HOST, PORTSCKT)
    get_all_disciplinas(HOST, PORTSCKT)
    serve()
