#!.venv/bin/python3
"""admin client"""

import argparse
import grpc
import portalADM_pb2 # Importa os módulos gerados pelo protobuf para as mensagens
import portalADM_pb2_grpc # Importa os módulos gerados pelo protobuf para os serviços


# command line arguments
def set_args():
    parser = argparse.ArgumentParser(
        prog='admin_client', description='Portal Administrativo client')
    parser.add_argument("--port", default=50051, type=int, help="server port")
    parser.add_argument("--op",
                        choices=[
                            "create",
                            "get",
                            "getall",
                            "update",
                            "delete",
                        ],
                        required=True,
                        help="the operation to perform on the server")
    parser.add_argument("--base",
                        choices=[
                            "aluno",
                            "professor",
                            "disciplina",
                        ],
                        required=True,
                        help="the base to update on the server")
    parser.add_argument(
        "--key",
        help=
        "one key, 'matricula' para 'alunos', 'siape' para 'professores, 'sigla' para 'disciplinas'"
    )
    parser.add_argument("--val",
                        nargs="+",
                        help="one or more values, depending on the operation")
    
    parser.add_argument("--test",
                        help="output expected return")
    return parser


def main():
    """main function"""
    args = set_args().parse_args()
    port = args.port or 50051
    with grpc.insecure_channel(f"127.0.0.1:{port}") as channel:
        print(f"args = {args}")
        stub = portalADM_pb2_grpc.PortalAdministrativoStub(channel)

        if args.base == "aluno":
            if args.op == "get":
                res = stub.ObtemAluno(portalADM_pb2.Identificador(id=args.key))
            elif args.op == "create":
                res = stub.NovoAluno(
                    portalADM_pb2.Aluno(matricula=args.key, nome=args.val[0]))
            elif args.op == "update":
                res = stub.EditaAluno(
                    portalADM_pb2.Aluno(matricula=args.key, nome=args.val[0]))
            elif args.op == "delete":
                res = stub.RemoveAluno(portalADM_pb2.Identificador(id=args.key))
            elif args.op == "getall":
                res = []
                for r in stub.ObtemTodosAlunos(portalADM_pb2.Vazia()):
                    res.append(r)
            else:
                res = ""
                print("Operação e/ou base inválidas.")

        elif args.base == "professor":
            if args.op == "get":
                res = stub.ObtemProfessor(portalADM_pb2.Identificador(id=args.key))
            elif args.op == "create":
                res = stub.NovoProfessor(
                    portalADM_pb2.Professor(siape=args.key, nome=args.val[0]))
            elif args.op == "update":
                res = stub.EditaProfessor(
                    portalADM_pb2.Professor(siape=args.key, nome=args.val[0]))
            elif args.op == "delete":
                res = stub.RemoveProfessor(portalADM_pb2.Identificador(id=args.key))
            elif args.op == "getall":
                res = []
                for r in stub.ObtemTodosProfessores(portalADM_pb2.Vazia()):
                    res.append(r)
            else:
                res = ""
                print("Operação inválida.")

        elif args.base == "disciplina":
            if args.op == "get":
                res = stub.ObtemDisciplina(portalADM_pb2.Identificador(id=args.key))
            elif args.op == "create":
                res = stub.NovaDisciplina(
                    portalADM_pb2.Disciplina(sigla=args.key,
                                      nome=args.val[0],
                                      vagas=int(args.val[1])))
            elif args.op == "update":
                res = stub.EditaDisciplina(
                    portalADM_pb2.Disciplina(sigla=args.key,
                                      nome=args.val[0],
                                      vagas=int(args.val[1])))
            elif args.op == "delete":
                res = stub.RemoveDisciplina(portalADM_pb2.Identificador(id=args.key))
            elif args.op == "getall":
                res = []
                for r in stub.ObtemTodasDisciplinas(portalADM_pb2.Vazia()):
                    res.append(r)
            else:
                res = ""
                print("Operação inválida.")

        else:
            res = ""
            print("Base inválida.")

        print(f"Response:\n{res}\n")


if __name__ == "__main__":
    main()
