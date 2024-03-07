#!/usr/bin/env python3
"""mat client"""

import grpc
import portalMat_pb2
import portalMat_pb2_grpc


def menu():
    print("Welcome to Portal Matricula client")
    print("1. Add Professor")
    print("2. Add Student")
    print("3. Delete Professor")
    print("4. Delete Student")
    print("5. DetalhaDisciplina")
    print("6. ObtemDisciplinasProfessor")
    print("7. ObtemDisciplinasAluno")
    print("0. Exit")
    choice = input("Enter your choice: ")
    return choice

def main():
    port = input("Enter port: ")
    with grpc.insecure_channel(f"127.0.0.1:{port}") as channel:
        stub = portalMat_pb2_grpc.PortalMatriculaStub(channel)

        while True:
            choice = menu()
            if choice == '1':
                disciplina = input("Enter Discipline: ")
                id_pessoa = input("Enter Professor ID: ")
                res= stub.AdicionaProfessor(portalMat_pb2.DisciplinaPessoa(disciplina=disciplina, idPessoa=id_pessoa))

            elif choice == '2':
                disciplina = input("Enter Discipline: ")
                id_pessoa = input("Enter Student ID: ")
                res= stub.AdicionaAluno(portalMat_pb2.DisciplinaPessoa(disciplina=disciplina, idPessoa=id_pessoa))
                
            elif choice == '3':
                disciplina = input("Enter Discipline: ")
                id_pessoa = input("Enter Professor ID: ")
                res= stub.RemoveProfessor(portalMat_pb2.DisciplinaPessoa(disciplina=disciplina, idPessoa=id_pessoa))
                
            elif choice == '4':
                disciplina = input("Enter Discipline: ")
                id_pessoa = input("Enter Student ID: ")
                res= stub.RemoveAluno(portalMat_pb2.DisciplinaPessoa(disciplina=disciplina, idPessoa=id_pessoa))
                
            elif choice == '5':
                id = input("Enter Discipline: ")
                res= stub.DetalhaDisciplina(portalMat_pb2.Identificador(id=id))
               
            elif choice == '6':
                id = ("Enter Professor ID: ")
                res = []
                res += stub.ObtemDisciplinasProfessor(portalMat_pb2.Identificador(id=id))
                
            elif choice == '7':
                id = ("Enter Student ID: ")
                res = []
                res += stub.ObtemDisciplinasAluno(portalMat_pb2.Identificador(id=id))
             
            elif choice == '0':
                print("Exiting...")
                break
            else:
                print("Invalid choice. Please try again.")

            print(f"Response:\n{res}\n")


if __name__ == "__main__":
    main()
