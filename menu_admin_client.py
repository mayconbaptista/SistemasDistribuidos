import grpc
import portalADM_pb2
import portalADM_pb2_grpc

def print_menu():
    print("MENU")
    print("1. Criar")
    print("2. Obter")
    print("3. Obter todos")
    print("4. Atualizar")
    print("5. Deletar")
    print("0. Sair")

def main():
    port = int(input("Port: ")) or 50051
    with grpc.insecure_channel(f"127.0.0.1:{port}") as channel:
        stub = portalADM_pb2_grpc.PortalAdministrativoStub(channel)

        while True:
            print_menu()
            choice = input("Escolha a operação: ")

            if choice == "0":
                print("Saindo do programa.")
                break

            base = input("Escolha a base (aluno, professor, disciplina): ")

            if base not in ["aluno", "professor", "disciplina"]:
                print("Base inválida.")
                continue

            if choice in ["1", "4"]:  # create or update
                key = input("Digite a chave (matricula para aluno, siape para professor, sigla para disciplina): ")
                val = input("Digite o valor: ")
            elif choice in ["2", "5"]:  # get or delete
                key = input("Digite a chave: ")

            if choice == "1":
                if base == "aluno":
                    res = stub.NovoAluno(portalADM_pb2.Aluno(matricula=key, nome=val))
                elif base == "professor":
                    res = stub.NovoProfessor(portalADM_pb2.Professor(siape=key, nome=val))
                elif base == "disciplina":
                    vagas = int(input("Digite o número de vagas: "))
                    res = stub.NovaDisciplina(portalADM_pb2.Disciplina(sigla=key, nome=val, vagas=vagas))

            elif choice == "2":
                if base == "aluno":
                    res = stub.ObtemAluno(portalADM_pb2.Identificador(id=key))
                elif base == "professor":
                    res = stub.ObtemProfessor(portalADM_pb2.Identificador(id=key))
                elif base == "disciplina":
                    res = stub.ObtemDisciplina(portalADM_pb2.Identificador(id=key))

            elif choice == "3":
                if base == "aluno":
                    res = []
                    for r in stub.ObtemTodosAlunos(portalADM_pb2.Vazia()):
                        res.append(r)
                elif base == "professor":
                    res = []
                    for r in stub.ObtemTodosProfessores(portalADM_pb2.Vazia()):
                        res.append(r)
                elif base == "disciplina":
                    res = []
                    for r in stub.ObtemTodasDisciplinas(portalADM_pb2.Vazia()):
                        res.append(r)

            elif choice == "4":
                if base == "aluno":
                    res = stub.EditaAluno(portalADM_pb2.Aluno(matricula=key, nome=val))
                elif base == "professor":
                    res = stub.EditaProfessor(portalADM_pb2.Professor(siape=key, nome=val))
                elif base == "disciplina":
                    vagas = int(input("Digite o novo número de vagas: "))
                    res = stub.EditaDisciplina(portalADM_pb2.Disciplina(sigla=key, nome=val, vagas=vagas))

            elif choice == "5":
                if base == "aluno":
                    res = stub.RemoveAluno(portalADM_pb2.Identificador(id=key))
                elif base == "professor":
                    res = stub.RemoveProfessor(portalADM_pb2.Identificador(id=key))
                elif base == "disciplina":
                    res = stub.RemoveDisciplina(portalADM_pb2.Identificador(id=key))

            print(f"Response:\n{res}\n")

if __name__ == "__main__":
    main()
