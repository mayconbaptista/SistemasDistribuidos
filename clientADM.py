
from __future__ import print_function

import grpc
import portalADM_pb2 # Importa os módulos gerados pelo protobuf para as mensagens
import portalADM_pb2_grpc # Importa os módulos gerados pelo protobuf para os serviços

from data import *
import os

def run(opt:int):
    
    response = []  # Cria uma variável para armazenar a resposta do servidor

    # Cria um canal de comunicação inseguro com o servidor gRPC
    with grpc.insecure_channel('localhost:50051') as channel:


        # Cria um stub (cliente) para o serviço definido no protobuf
        stub = portalADM_pb2_grpc.PortalAdministrativoStub(channel)

        if(opt == 1 ):
            # Chama o método Aluno do servidor
            matricula = input("Entre com a matricula: ") 
            nome = input("Entre com o nome: ")
            response = stub.NovoAluno(portalADM_pb2.Aluno(matricula=matricula, nome=nome)) # testado ok

        elif (opt == 2):
            # chama o método EditaAluno do servidor
            matricula = input("Entre com a matricula do aluno que deseja editar: ")
            newNome = input("Entre com o novo nome do aluno: ")
            response = stub.EditaAluno(portalADM_pb2.Aluno(matricula=matricula, nome=newNome)) # testado ok
        
        elif(opt == 3):
            # clama o método RemoveAluno do servidor 
            matricula = input("Entre a matricula do aluno que deseja remover: ")
            response = stub.RemoveAluno(portalADM_pb2.Identificador(id=matricula))

        elif(opt == 4):
            print("Alunos:")
            response = stub.ObtemTodosAlunos(portalADM_pb2.Vazia())

            for aluno in response:
                print(aluno)
            pass
    
    print(response)  # Imprime a resposta recebida do servidor


if __name__ == '__main__':

    while(True):
        opt = int(input("1:Add\n2:Edita\n3:Remove\n4:GetAll\nEntre com a opção: "))
        
        if (opt == 0):
            break
        
        run(opt)  # Executa a função run() ao rodar o script