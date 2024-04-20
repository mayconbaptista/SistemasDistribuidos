from __future__ import print_function

import sys
import plyvel
import socket
import json
sys.path.append("../")
from pysyncobj import SyncObj, SyncObjConf, replicated

class KVStorage(SyncObj):
    def __init__(self, selfAddress, partnerAddrs, db_path):
        cfg = SyncObjConf(dynamicMembershipChange=True)
        super(KVStorage, self).__init__(selfAddress, partnerAddrs, cfg)
        self._aluno = plyvel.DB(db_path + "/alunos", create_if_missing=True)
        self._professor = plyvel.DB(db_path + "/professores", create_if_missing=True)
        self._disciplina = plyvel.DB(db_path + "/disciplinas", create_if_missing=True)


    # region put
    @replicated
    def setAluno(self, key, json_value):
        self._aluno.put(key.encode('utf-8'), json_value.encode('utf-8'))

    @replicated
    def setProfessor(self, key, json_value):
        self._professor.put(key.encode('utf-8'), json_value.encode('utf-8'))

    @replicated
    def setDisciplina(self, key, json_value):
        self._disciplina.put(key.encode('utf-8'), json_value.encode('utf-8'))

    # region pop
    @replicated
    def popAluno(self, key):
        value = self._aluno.get(key.encode('utf-8'))
        if value:
            self._aluno.delete(key.encode('utf-8'))
        return value.decode('utf-8') if value else None

    @replicated
    def popProfessor(self, key):
        value = self._professor.get(key.encode('utf-8'))
        if value:
            self._professor.delete(key.encode('utf-8'))
        return value.decode('utf-8') if value else None
    
    @replicated
    def popDisciplina(self, key):
        value = self._disciplina.get(key.encode('utf-8'))
        if value:
            self._disciplina.delete(key.encode('utf-8'))
        return value.decode('utf-8') if value else None

    #region get
    def getAluno(self, key):
        value = self._aluno.get(key.encode('utf-8'))
        return value.decode('utf-8') if value else None
    
    def getProfessor(self, key):
        value = self._professor.get(key.encode('utf-8'))
        return value.decode('utf-8') if value else None
    
    def getDisciplina(self, key):
        value = self._disciplina.get(key.encode('utf-8'))
        return value.decode('utf-8') if value else None

    def getAllAlunos(self):
        items = {}
        for key, value in self._aluno:
            items[key.decode('utf-8')] = value.decode('utf-8')
        return items
    
    def getAllProfessores(self):
        items = {}
        for key, value in self._professor:
            items[key.decode('utf-8')] = value.decode('utf-8')
        return items
    
    def getAllDisciplinas(self):
        items = {}
        for key, value in self._disciplina:
            items[key.decode('utf-8')] = value.decode('utf-8')
        return items
_g_kvstorage = None

def main():
    if len(sys.argv) < 4:
        print('Usage: %s selfHost:port db_path server_port partner1Host:port partner2Host:port ...' % sys.argv[0])
        sys.exit(-1)

    selfAddr = sys.argv[1]
    db_path = sys.argv[2]
    server_port = int(sys.argv[3])
    partners = sys.argv[4:]

    global _g_kvstorage
    _g_kvstorage = KVStorage(selfAddr, partners, db_path)

    # Set up the server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', server_port))
    server_socket.listen(5)
    print('Server is running on port %d' % server_port)

    try:
        while True:
            client_socket, addr = server_socket.accept()
            with client_socket:
                print('Connected by', addr)
                while True:
                    data = client_socket.recv(1024).decode('utf-8').strip()
                    if not data:
                        break
                    try:
                        cmd = json.loads(data)
                        action = cmd.get('action')
                        key = cmd.get('key')
                        if action == 'setaluno' and 'value' in cmd:
                            _g_kvstorage.setAluno(key, json.dumps(cmd['value']))
                            client_socket.sendall(b'OK\n')
                        elif action == 'getaluno':
                            value = _g_kvstorage.getAluno(key)
                            client_socket.sendall((value + '\n' if value else 'None\n').encode('utf-8'))
                        elif action == 'popaluno':
                            result = _g_kvstorage.popAluno(key)
                            client_socket.sendall((result + '\n' if result else 'None\n').encode('utf-8'))
                        elif action == 'getallalunos':
                            items = _g_kvstorage.getAllAlunos()
                            client_socket.sendall(json.dumps(items).encode('utf-8') + b'\n')
                        elif action == 'setprofessor' and 'value' in cmd:
                            _g_kvstorage.setProfessor(key, json.dumps(cmd['value']))
                            client_socket.sendall(b'OK\n')
                        elif action == 'getprofessor':
                            value = _g_kvstorage.getProfessor(key)
                            client_socket.sendall((value + '\n' if value else 'None\n').encode('utf-8'))
                        elif action == 'popprofessor':
                            result = _g_kvstorage.popProfessor(key)
                            client_socket.sendall((result + '\n' if result else 'None\n').encode('utf-8'))
                        elif action == 'getallprofessores':
                            items = _g_kvstorage.getAllProfessores()
                            client_socket.sendall(json.dumps(items).encode('utf-8') + b'\n')
                        elif action == 'setdisciplina' and 'value' in cmd:
                            _g_kvstorage.setDisciplina(key, json.dumps(cmd['value']))
                            client_socket.sendall(b'OK\n')
                        elif action == 'getdisciplina':
                            value = _g_kvstorage.getDisciplina(key)
                            client_socket.sendall((value + '\n' if value else 'None\n').encode('utf-8'))
                        elif action == 'popdisciplina':
                            result = _g_kvstorage.popDisciplina(key)
                            client_socket.sendall((result + '\n' if result else 'None\n').encode('utf-8'))
                        elif action == 'getalldisciplinas':
                            items = _g_kvstorage.getAllDisciplinas()
                            client_socket.sendall(json.dumps(items).encode('utf-8') + b'\n')
                        else:
                            client_socket.sendall(b'Error: Wrong command\n')
                    except json.JSONDecodeError:
                        client_socket.sendall(b'Error: Invalid JSON\n')
    finally:
        server_socket.close()

if __name__ == '__main__':
    main()
