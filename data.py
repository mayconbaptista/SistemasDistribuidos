class Aluno () :
    matricula:str
    nome:str

    def __init__(self, matricula, nome) -> None:

        if(len(matricula) < 4 or len(nome) < 4):
            raise ValueError("Os campos nome e matricula devem ter mais de 4 caractares")
        
        self.matricula = matricula
        self.nome = nome

class Professor ():
    siape:str
    nome:str

    def __init__(self, siape, nome) -> None:

        if(len(siape) < 4 or len(nome) < 4):
            raise ValueError("Os campos siape e nome devem ter mais de 4 caractares")
        self.siape = siape
        self.nome = nome


class Disciplina ():
    sigla:str
    nome:str
    vagas:int # total de alunos permitido

    def __init__(self, sigla, nome, vagas) -> None:

        if(len(nome) < 4 or vagas <= 0):
            raise ValueError("Os campos sigla e nome devem ter mais de 4 caractares, alem de vagas maior que 1")

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

        if(len(id) < 4):
            raise ValueError("Bad request")
        
        self.id = id
