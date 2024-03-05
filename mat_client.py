#!.venv/bin/python3
"""mat client"""

import argparse
import sys

import grpc
import portalMat_pb2
import portalMat_pb2_grpc

# command line arguments
def set_args():
    parser = argparse.ArgumentParser(prog='mat_client',
                                     description='Portal Matricula client')
    parser.add_argument("--port", default=50051, type=int, help="server port")
    parser.add_argument("--op",
                        choices=[
                            "add_prof",
                            "add_aluno",
                            "del_prof",
                            "del_aluno",
                            "rel_disc",
                            "rel_prof",
                            "rel_aluno",
                        ],
                        required=True,
                        help="the operation to perform on the server")
    parser.add_argument("--val",
                        nargs="+",
                        help="one or more values, depending on the operation")
    return parser


def main():
    """main function"""
    args = set_args().parse_args()
    port = args.port or 50051
    with grpc.insecure_channel(f"127.0.0.1:{port}") as channel:
        print(f"args = {args}")
        stub = portalMat_pb2_grpc.PortalMatriculaStub(channel)

        if args.op == "add_prof":
            res = stub.AdicionaProfessor(
                portalMat_pb2.DisciplinaPessoa(disciplina=args.val[0],
                                        idPessoa=args.val[1]))
        elif args.op == "add_aluno":
            res = stub.AdicionaAluno(
                portalMat_pb2.DisciplinaPessoa(disciplina=args.val[0],
                                        idPessoa=args.val[1]))
        elif args.op == "del_prof":
            res = stub.RemoveProfessor(
                portalMat_pb2.DisciplinaPessoa(disciplina=args.val[0],
                                        idPessoa=args.val[1]))
        elif args.op == "del_aluno":
            res = stub.RemoveAluno(
                portalMat_pb2.DisciplinaPessoa(disciplina=args.val[0],
                                        idPessoa=args.val[1]))
        elif args.op == "rel_disc":
            res = stub.DetalhaDisciplina(portalMat_pb2.Identificador(id=args.val[0]))
        elif args.op == "rel_prof":
            res = []
            res += stub.ObtemDisciplinasProfessor(
                portalMat_pb2.Identificador(id=args.val[0]))
        elif args.op == "rel_aluno":
            res = []
            res += stub.ObtemDisciplinasAluno(
                portalMat_pb2.Identificador(id=args.val[0]))
        else:
            res = ""
            print("Operação e/ou base inválidas.")

        print(f"Response:\n{res}\n")


if __name__ == "__main__":
    main()
