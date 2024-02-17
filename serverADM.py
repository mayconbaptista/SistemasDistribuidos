from concurrent import futures
import logging

import grpc

import portalADM_pb2
import portalADM_pb2_grpc

from data import * # dados auxiliares

dados = dict()

def imprime ():
    for key, value in dados.items():
        print(f"{key} | {value.matricula} - {value.nome}")

# classe portalAdministrativo que conterá as funções clamadas via RPC
class PortalAdministrativo (portalADM_pb2_grpc.PortalAdministrativoServicer):

    # Método para manipular a solicitação GetUsers
    def NovoAluno(self, request, context): # ok
        try:
            if(request.matricula and len(request.nome)):
                if(len(request.matricula) < 4 or len(request.nome) < 4):
                    return portalADM_pb2.Status(status=1, msg=f"Os campos matricula e nome devem ter mais de 4 caracteres!")
                
                dados[request.matricula] = Aluno(matricula=request.matricula,nome=request.nome) # quardando os dados dos alunos
                imprime()
                return portalADM_pb2.Status(status=0, msg=f"Aluno {request.nome} cadastrado com suceso!.")
            else:
                return portalADM_pb2.Status(status=1, msg=f"A matricula {request.matricula} já existe!")
        
        except Exception as e:
            return portalADM_pb2.Status(status=1, msg=f"Erro: {str(e)}")
    
    def EditaAluno(self, request, context): # ok
        try:
            if(dados.get(request.matricula)):
                if(len(request.matricula) < 4 or len(request.nome) < 4):
                    return portalADM_pb2.Status(status=1, msg=f"Os campos matricula e nome devem ter mais de 4 caracteres!")
                
                dados[request.matricula] = Aluno(matricula=request.matricula, nome=request.nome)
                print(dados.get(request.matricula))
                imprime()
                return portalADM_pb2.Status(status=0, msg=f"Aluno {request.nome} Editado com sucesso!.")
            else:
                return portalADM_pb2.Status(status=1, msg=f"Erro a matricula {request.matricula} Não existe")
            
        except Exception as e:
            return portalADM_pb2.Status(status=1, msg=f"Erro: {str(e)}")
    
    def RemoveAluno(self, request, context): # ok

        try:
            dados.pop(request.id)
            imprime()
            return portalADM_pb2.Status(status=0, msg=f"Aluno {request.id} removido com sucesso!")
        except Exception as e:
            return portalADM_pb2.Status(status=0, msg=f"Error: {str(e)}")
        
    def ObtemAluno(self, request, context):

        try:
            if(dados.get(request.id)):
                aluno = dados.get(request.id)
                return portalADM_pb2.Aluno(matricula=aluno.matricula, nome=aluno.nome)
            else:
                return portalADM_pb2.Aluno(matricula="", nome="")
        except Exception as e:
            return portalADM_pb2.Aluno(matricula="", nome="")

    def ObtemTodosAlunos(self, request, context):
        return super().ObtemTodosAlunos(request, context)




# Função para iniciar o servidor gRPC
def serve():
    # Criação do servidor gRPC com um pool de threads
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Registro do serviço PortalAdmistrativo na instância do servidor
    portalADM_pb2_grpc.add_PortalAdministrativoServicer_to_server(PortalAdministrativo(), server)

    # Adiciona uma porta de escuta não segura (insecure) no servidor
    server.add_insecure_port('[::]:50051')

    # Inicia o servidor
    server.start()

    # Aguarda a finalização do servidor
    server.wait_for_termination()


if __name__ == '__main__':
    # Configuração do logging básico
    logging.basicConfig()
    print("Starting server in: %s" % ('localhost:50051'))

    # Inicia o servidor
    serve()