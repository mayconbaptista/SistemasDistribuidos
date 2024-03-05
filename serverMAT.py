#!.venv/bin/python3
import sys
import json
import paho.mqtt.client as mqtt
import grpc
import logging
from concurrent import futures
# arquivo gerado apartir do portalADM.proto 
import portalMat_pb2
import portalMat_pb2_grpc

from data import * # dados auxiliares

############################################## Variaveis globais #####################################

# Configurações do servidor
HOST = '127.0.0.1'
PORT = int(input("Host: "))

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

###################################### Funções do da conecção do mqtt ############################################

def on_connect(client, userdata, flags, reason_code, properties):

    if reason_code.is_failure:
        print(f"Falha ao conectar: ​{reason_code}. loop_forever() tentará novamente a conexão")
        sys.exit(1)
    else:
        # assinamdo o retorno de chamada on_connect para ter certeza
        # nossa assinatura persiste nas reconexões.
        # subescrevendo em toda a arvore de tópicos até a raiz portal
        client.subscribe(MQTT_TOPIC_BASE + "#")

# Função para lidar com mensagens recebidas do broker MQTT
def on_message(client, userdata, msg):

    print(f"Mensagem recebida do tópico -> {msg.topic}: {msg.payload.decode()}")

    payload = json.loads(msg.payload.decode())

    if(str(msg.topic).find("aluno") > -1):
        MQTT_sincronize_aluno(msg.topic, payload) #ok
    elif(str(msg.topic).find("professor") > -1):
        MQTT_sincronize_professor(msg.topic, payload)
    elif(str(msg.topic).find("disciplina") > -1):
        MQTT_sincronize_disciplina(msg.topic, payload)

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

                            disciplina["vagas"] += 1

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

                    dados_json = json.dumps({"sigla":request.disciplina, "idPessoa":request.idPessoa, "vagas":disciplina.get("vagas")})

                    # Publica mensagem MQTT indicando a remoção de um aluno da disciplina
                    mqtt_client.publish(MQTT_TOPIC_BASE + "mat/aluno/del/", dados_json, 0)
                    
                    return portalMat_pb2.Status(status=STATUS_OK, msg="OK")
                else:
                    return portalMat_pb2.Status(status=STATUS_ERROR, msg=f"Not_found alundoId{request.idPessoa}")
            else:
                return portalMat_pb2.Status(status=STATUS_ERROR, msg=f"Not_found disciplinaId:{request.disciplina}")
        except Exception as e:
            return portalMat_pb2.Status(status=STATUS_ERROR, msg=f"Bad_request alunoId:{request.idPessoa} not in disciplinaId:{request.disciplina}")

    def DetalhaDisciplina(self, request, context):

        try:
            if request.id in matriculas.keys():

                disciplina = json.loads(disciplinas.get(request.id))

                disciplina = portalMat_pb2.Disciplina(sigla=disciplina.get("sigla"), nome=disciplina.get("nome"), vagas=int(disciplina.get("vagas")))

                professor = professores.get(disciplina.get())

                alunos = [portalMat_pb2.Aluno(matricula=matricula, nome=alunos[matricula]) for matricula in disciplina.get('alunos', [])]
                relatorio = portalMat_pb2.RelatorioDisciplina(disciplina=portalMat_pb2.Disciplina(sigla=request.id, nome=disciplina.get('nome', ''), vagas=disciplina.get('vagas', 0)), professor=professor, alunos=alunos)
                return relatorio
            else:
                disciplina_error = portalMat_pb2.Disciplina(sigla=" ", nome=" ", vagas=0)
                professor_error = portalMat_pb2.Professor(siape="", nome="")
                return portalMat_pb2.RelatorioDisciplina(disciplina = disciplina_error, professor=professor_error, alunos=[])
        except Exception as e:
            return portalMat_pb2.RelatorioDisciplina()
        
    def ObtemDisciplinasProfessor(self, request, context):
        
        for values in matriculas.values():
            if request.id in values:
                return

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

if __name__ == '__main__':
    # Configuração do logging básico
    logging.basicConfig()
    print("Iniciando servidor em: %s" % (f'localhost:{PORT}'))

    # Inicia o servidor
    serve()