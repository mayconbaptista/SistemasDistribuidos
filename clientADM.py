from __future__ import print_function

import grpc
import portalADM_pb2 # Importa os módulos gerados pelo protobuf para as mensagens
import portalADM_pb2_grpc # Importa os módulos gerados pelo protobuf para os serviços

from data import *

def run(opt:int):
    
    response = []  # Cria uma variável para armazenar a resposta do servidor

    # Cria um canal de comunicação inseguro com o servidor gRPC
    with grpc.insecure_channel('localhost:50051') as channel:


        # Cria um stub (cliente) para o serviço definido no protobuf
        stub = portalADM_pb2_grpc.PortalAdministrativoStub(channel)

        if(opt == 1 ):
            # Chama o método Aluno do servidor
            response = stub.NovoAluno(portalADM_pb2.Aluno(matricula='11921BSI209', nome='Maycon Douglas')) # testado ok

        elif (opt == 2):
            # chama o método EditaAluno do servidor
            response = stub.EditaAluno(portalADM_pb2.Aluno(matricula='11921BSI209', nome='Maycon Douglas Batista dos santos')) # testado ok

    print(response)  # Imprime a resposta recebida do servidor


if __name__ == '__main__':

    while(True):

        opt = int(input("Entre com a opção: "))
        
        if (opt == 0):
            break
        
        run(opt)  # Executa a função run() ao rodar o script