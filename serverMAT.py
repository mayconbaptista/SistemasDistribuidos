#!.venv/bin/python3
import sys
import json
import paho.mqtt.client as mqtt
import grpc
import logging
import socket
from concurrent import futures
# arquivo gerado apartir do portalADM.proto 
import portalMat_pb2
import portalMat_pb2_grpc

from data import * # dados auxiliares

############################################## Variaveis globais #####################################

# Configurações do servidor
HOST = '127.0.0.1'
PORT = int(input("Host: "))
PORTSCKT= int(input("Socket Host: "))

# Configurações do broker MQTT
MQTT_BROKER_HOST = '127.0.0.1' # 'mqtt.eclipseprojects.io'
MQTT_BROKER_PORT = 1883
MQTT_TOPIC_BASE = 'portal/'

alunos      = {}
professores = {}
disciplinas = {}
matriculas  = {}

STATUS_OK    = 0
STATUS_ERROR = 1

###################################### funções de sincronização de dados entre servidores ######################

def MQTT_sincronize_aluno (event, request):

    try:
        if(str(event).endswith("create")):

            if(not request.get("matricula") in alunos.keys()):

                alunos[request.get("matricula")] = json.dumps(request)

        elif (str(event).endswith("update")):

            if(request.get("matricula") in alunos.keys()):

                alunos[request.get("matricula")] = json.dumps(request)

        elif(str(event).endswith("delete")):

            alunos.pop(request.get("matricula"))

    except Exception as e:
        print(f"Sincronize Error: {str(e)}")
        

def MQTT_sincronize_professor (event, request):
    try:
        if(str(event).endswith("create")):

            if(not request.get("siape") in professores.keys()):

                professores[request.get("siape")] = json.dumps(request)

        elif (str(event).endswith("update")):

            if(request.get("siape") in professores.keys()):

                professores[request.get("siape")] = json.dumps(request)

        elif(str(event).endswith("delete")):

            professores.pop(request.get("siape"))
    except Exception as e:
        print(f"Sincronize Error: {str(e)}")
        

def MQTT_sincronize_disciplina (event, request):
    try:
        if(str(event).endswith("create")):

            if(not request.get("sigla") in disciplinas.keys()):

                disciplinas[request.get("sigla")] = json.dumps(request)

                matriculas[request.get("sigla")] = {"alunos":[], "professor":None}
        
        elif(str(event).endswith("update")):

            if(request.get("sigla") in disciplinas.keys()):

                disciplinas[request.get("sigla")] = json.dumps(request)

        elif(str(event).endswith("delete")):

            if(request.get("sigla") in disciplinas.keys()):

                disciplinas.pop(request.get("sigla"))

                matriculas.pop(request.get("sigla"))

    except Exception as e:
        print(f"Sincronize Error: {str(e)}")


def MQTT_sincronize_with_mat (event, request):

    try:
        if(str(event).endswith("add")):

            if(str(event).find("prof") > -1):

                if(matriculas.get(request.get("disciplina")).get("professor") is None):

                    professor = json.loads(professores.get(request.get("idPessoa")))
                    matriculas[request.get("disciplina")]["professor"] = professor
                    return
                
            elif(str(event).find("aluno") > -1):

                disciplina = json.loads(disciplinas.get(request.get("disciplina")))

                if int(disciplina.get("vagas")) > 0:

                    if(not request.get("idPessoa") in matriculas[request.get("disciplina")]['alunos']):# aqui!

                        disciplina["vagas"] -= 1

                        disciplinas[request.get("disciplina")] = json.dumps(disciplina)

                        matriculas[request.get("disciplina")]["alunos"].append(request.get("idPessoa"))

                        return
                
        elif(str(event).endswith("del") > -1):

            if(str(event).find("prof") > -1):

                if (request.get("idPessoa") == matriculas[request.get("disciplina")]['professor']['siape']):

                    matriculas[request.get("disciplina")]['professor'] = None

                    return
                
            if(str(event).find("aluno") > -1 ):

                matriculas[request.get("disciplina")]['alunos'].remove(request.get("idPessoa"))

                disciplina = json.loads(disciplinas.get(request.get("disciplina")))

                disciplina['vagas'] += 1

                disciplinas[request.get("disciplina")] = json.dumps(disciplina)

                return
            
    except Exception as e:
        print(f"Sincronize Error: {str(e)}")


###################################### Funções do da conecção do mqtt ############################################

def on_connect(client, userdata, flags, reason_code, properties):

    if reason_code.is_failure:
        print(f"Falha ao conectar: ​{reason_code}. loop_forever() tentará novamente a conexão")
        sys.exit(1)
    else:
        # assinamdo o retorno de chamada on_connect para ter certeza
        # nossa assinatura persiste nas reconexões.
        # subescrevendo em toda a arvore de tópicos até a raiz portal
        client.subscribe("portal/" + "#")

# Função para lidar com mensagens recebidas do broker MQTT
def on_message(client, userdata, msg):

    print(f"Mensagem recebida do tópico -> {msg.topic}: {msg.payload.decode()}")

    payload = json.loads(msg.payload.decode())

    if(str(msg.topic).find("admin") > -1):
        if(str(msg.topic).find("aluno") > -1):
            MQTT_sincronize_aluno (msg.topic, payload) #ok
        elif(str(msg.topic).find("professor") > -1):
            MQTT_sincronize_professor(msg.topic, payload)
        elif(str(msg.topic).find("disciplina") > -1):
            MQTT_sincronize_disciplina(msg.topic, payload)

    elif(str(msg.topic).find("mat") > -1):
        MQTT_sincronize_with_mat (msg.topic, payload)
    

# Configuração do cliente MQTT
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

######################################### Classes com as funções chamadas via RPC #####################################

# Implementação do serviço Disciplina
class PortalMatricula(portalMat_pb2_grpc.PortalMatriculaServicer):

    def AdicionaProfessor(self, request, context):

        try:
            if(request.disciplina in disciplinas.keys()):

                if(request.idPessoa in professores.keys()):

                    if(matriculas.get(request.disciplina).get("professor") is None):

                        professor = json.loads(professores.get(request.idPessoa))

                        matriculas[request.disciplina]["professor"] = professor

                        dados_jason = json.dumps({"disciplina":request.disciplina, "idPessoa":request.idPessoa})

                        # Publica mensagem MQTT indicando a adição de um professor à disciplina
                        mqtt_client.publish(MQTT_TOPIC_BASE + "mat/professor/add", dados_jason, 0)
                        return portalMat_pb2.Status(status=STATUS_OK, msg="Ok")
                    else:
                        return portalMat_pb2.Status(status=STATUS_ERROR, msg=f"Conflict já tem professor nessa disciplina")
                else:
                    return portalMat_pb2.Status(status=STATUS_ERROR, msg=f"Not_found professorId:{request.idPessoa}")
            else: 
                return portalMat_pb2.Status(status=STATUS_ERROR, msg=f"Not_Found disciplinaId:{request.disciplina}")
        except Exception as e:
            return portalMat_pb2.Status(status=STATUS_ERROR, msg=f"Bad_request {str(e)}")
        
    def RemoveProfessor(self, request, context):

        try:
            if request.disciplina in disciplinas.keys():

                if request.idPessoa in professores.keys():

                    if(request.idPessoa == matriculas[request.disciplina]['professor']['siape']):

                        matriculas[request.disciplina]['professor'] = None

                        dados_json = json.dumps({"disciplina":request.disciplina, "idPessoa":request.idPessoa})

                        # Publica mensagem MQTT indicando a remoção de um professor da disciplina
                        mqtt_client.publish(MQTT_TOPIC_BASE + "mat/professor/del", dados_json, 0)

                        return portalMat_pb2.Status(status=STATUS_OK, msg="Ok")
                    else:
                        return portalMat_pb2.Status(status=STATUS_ERROR, msg=f"Not_found: professorId:{request.idPessoa} not in disciplinaId{request.disciplina}")
                else:
                    return portalMat_pb2.Status(status=STATUS_ERROR, msg=f"Not_found: professorId:{request.idPessoa}")
            else:
                return portalMat_pb2.Status(status=STATUS_ERROR, msg=f"Not_found DisciplinaId:{request.disciplina}")
        except Exception as e:
            return portalMat_pb2.Status(status=STATUS_ERROR, msg=f"Bad_request: idPessoa:{request.idPessoa} not in idPessoa:{request.disciplina}")

    def AdicionaAluno(self, request, context):

        try:

            if request.disciplina in disciplinas.keys():

                if request.idPessoa in alunos.keys():

                    disciplina = json.loads(disciplinas.get(request.disciplina))

                    if int(disciplina.get("vagas")) > 0:

                        if(not request.idPessoa in matriculas[request.disciplina]['alunos']):# aqui!

                            disciplina["vagas"] -= 1

                            disciplinas[request.disciplina] = json.dumps(disciplina)

                            matriculas[request.disciplina]["alunos"].append(request.idPessoa)

                            dados_json = json.dumps({"disciplina":request.disciplina, "idPessoa":request.idPessoa, "vagas":disciplina.get("vagas")})

                            # Publica mensagem MQTT indicando a adição de um aluno à disciplina
                            mqtt_client.publish(MQTT_TOPIC_BASE + "mat/aluno/add", dados_json, 0)

                            return portalMat_pb2.Status(status=STATUS_OK, msg="Ok")
                        else:
                            return portalMat_pb2.Status(status=STATUS_ERROR, msg=f"Conflict idPessoa:{request.idPessoa}")
                    else:
                        return portalMat_pb2.Status(status=STATUS_ERROR, msg=f"Conflict vagas:0")
                else:
                    return portalMat_pb2.Status(status=STATUS_ERROR, msg=f"Not_found alunoId:{request.idPessoa}")
            else:
                return portalMat_pb2.Status(status=STATUS_ERROR, msg=f"Not_found disciplinaId:{request.disciplina}")
            
        except Exception as e:
            return portalMat_pb2.Status(status=STATUS_ERROR, msg=f"Bad_request: {str(e)}")

    def RemoveAluno(self, request, context):

        try:

            if request.disciplina in matriculas.keys():

                if request.idPessoa in alunos.keys():

                    matriculas[request.disciplina]['alunos'].remove(request.idPessoa)

                    disciplina = json.loads(disciplinas.get(request.disciplina))

                    disciplina['vagas'] += 1

                    disciplinas[request.disciplina] = json.dumps(disciplina)

                    dados_json = json.dumps({"disciplina":request.disciplina, "idPessoa":request.idPessoa, "vagas":disciplina.get("vagas")})

                    # Publica mensagem MQTT indicando a remoção de um aluno da disciplina
                    mqtt_client.publish(MQTT_TOPIC_BASE + "mat/aluno/del", dados_json, 0)
                    
                    return portalMat_pb2.Status(status=STATUS_OK, msg="OK")
                else:
                    return portalMat_pb2.Status(status=STATUS_ERROR, msg=f"Not_found alundoId{request.idPessoa}")
            else:
                return portalMat_pb2.Status(status=STATUS_ERROR, msg=f"Not_found disciplinaId:{request.disciplina}")
        except Exception as e:
            return portalMat_pb2.Status(status=STATUS_ERROR, msg=f"Bad_request alunoId:{request.idPessoa} not in disciplinaId:{request.disciplina}")

    def DetalhaDisciplina(self, request, context):
        try:
            if request.id in disciplinas.keys():
                disciplina_info = json.loads(disciplinas.get(request.id))
                professor_info = None
            
                if matriculas.get(request.id) and matriculas[request.id]['professor']:
                    professor_info = json.loads(professores.get(matriculas[request.id]['professor']['siape']))

                alunos_info = []
                for matricula in matriculas.get(request.id, {}).get('alunos', []):
                    aluno_info = json.loads(alunos.get(matricula))
                    alunos_info.append(portalMat_pb2.Aluno(matricula=matricula, nome=aluno_info.get('nome')))

                disciplina = portalMat_pb2.Disciplina(
                    sigla=disciplina_info.get('sigla', ''),
                    nome=disciplina_info.get('nome', ''),
                    vagas=int(disciplina_info.get('vagas', 0))
                )

                professor = portalMat_pb2.Professor(
                    siape=professor_info.get('siape', ''),
                    nome=professor_info.get('nome', '') if professor_info else ''
                ) if professor_info else None

                return portalMat_pb2.RelatorioDisciplina(
                    disciplina=disciplina,
                    professor=professor,
                    alunos=alunos_info
                )
            else:
                disciplina_error = portalMat_pb2.Disciplina(sigla=" ", nome=" ", vagas=0)
                professor_error = portalMat_pb2.Professor(siape="", nome="")
                return portalMat_pb2.RelatorioDisciplina(disciplina = disciplina_error, professor=professor_error, alunos=[])
        except Exception as e:
            print(f"Error in DetalhaDisciplina: {str(e)}")
            return portalMat_pb2.RelatorioDisciplina()

        
        
    def ObtemDisciplinasProfessor(self, request, context):
        try:
            for disciplina, matricula_info in matriculas.items():
                if matricula_info['professor'] and matricula_info['professor']['siape'] == request.id:
                    alunos_info = []
                    for matricula_aluno in matricula_info['alunos']:
                        aluno_info = json.loads(alunos.get(matricula_aluno))
                        alunos_info.append(portalMat_pb2.Aluno(matricula=matricula_aluno, nome=aluno_info.get('nome')))
                    yield portalMat_pb2.ResumoDisciplina(
                        disciplina=portalMat_pb2.Disciplina(
                            sigla=disciplina,
                            nome=json.loads(disciplinas.get(disciplina)).get('nome'),
                            vagas=int(json.loads(disciplinas.get(disciplina)).get('vagas', 0))
                        ),
                        professor=portalMat_pb2.Professor(
                            siape=request.id,
                            nome=json.loads(professores.get(request.id)).get('nome')
                        ),
                        totalAlunos=len(alunos_info)
                    )
        except Exception as e:
            print(f"Error in ObtemDisciplinasProfessor: {str(e)}")
            yield portalMat_pb2.ResumoDisciplina()

            

        
            
    def ObtemDisciplinasAluno(self, request, context):
        try:
            for disciplina, matricula_info in matriculas.items():
                if request.id in matricula_info['alunos']:
                    disciplina_info = json.loads(disciplinas.get(disciplina))
                    professor_info = None

                    if matricula_info['professor']:
                        professor_info = json.loads(professores.get(matricula_info['professor']['siape']))

                    alunos_info = []
                    for matricula_aluno in matricula_info['alunos']:
                        aluno_info = json.loads(alunos.get(matricula_aluno))
                        alunos_info.append(portalMat_pb2.Aluno(matricula=matricula_aluno, nome=aluno_info.get('nome')))

                    disciplina_proto = portalMat_pb2.Disciplina(
                        sigla=disciplina_info.get('sigla', ''),
                        nome=disciplina_info.get('nome', ''),
                        vagas=int(disciplina_info.get('vagas', 0))
                    )

                    professor_proto = portalMat_pb2.Professor(
                        siape=professor_info.get('siape', ''),
                        nome=professor_info.get('nome', '') if professor_info else ''
                    ) if professor_info else None

                    yield portalMat_pb2.ResumoDisciplina(
                        disciplina=disciplina_proto,
                        professor=professor_proto,
                        totalAlunos=len(alunos_info)
                    )

        except Exception as e:
            print(f"Error in ObtemDisciplinasAluno: {str(e)}")
            yield portalMat_pb2.ResumoDisciplina()

# Função para iniciar o servidor gRPC
def serve():

    # Criação do servidor gRPC com um pool de threads
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Registro do serviço PortalMatricula na instância do servidor
    portalMat_pb2_grpc.add_PortalMatriculaServicer_to_server(PortalMatricula(), server)

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
                alunos[key] = value
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
                professores[key] = value
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
                disciplinas[key] = value
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
