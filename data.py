class Aluno () :
    matricula:str
    nome:str

    def __init__(self, matricula, nome) -> None:
        self.matricula = matricula
        self.nome = nome

class Professor ():
    siape:str
    nome:str

    def __init__(self, siape, nome) -> None:
        self.siape = siape
        self.nome = nome


class Disciplina ():
    sigla:str
    nome:str
    vagas:int # total de alunos permitido

    def __init__(self, sigla, nome, vagas) -> None:
        self.sigla = sigla
        self.nome = nome
        self.vagas = vagas

class Status ():
    status:int # 0 = sucesso, 1 = erro
    msg:str # detalhes do erro para status = 1

    def __init__(self, status, msg) -> None:
        self.status = status
        self.msg = msg

class Identificador ():
    id:str # matricula, siape ou sigla

    def __init__(self, id:str) -> None:
        self.id = id
