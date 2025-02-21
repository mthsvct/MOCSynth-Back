import copy
import json
import datetime as dt
from dateutil import rrule
import random
import os
import zipfile

from .arquivo import *
from .horarios import *


class Gerador():

    def __init__(self, 
            indice=0, 
            pasta='./arqs', 
            intervalo=15, 
            result=None, 
            case=1, 
            date_initial=None, 
            date_final=None, 
            requisitos_selecionados=[],
            ms_selecionados=[]
        ):
        self.date_initial = date_initial #...... Data inicial do monitoramento
        self.date_final = date_final #.......... Data final do monitoramento
        self.name_app = None #.................. Nome do app;
        self.microsservices = None #............ Microsserviços extraídos do arquivo result;
        self.pasta = pasta #.................... Pasta onde será salvo o caminho;
        self.case = case #...................... Caso a ser gerado que será selecionado na função selectCase()
        self.result = result #.................. Aqui estarão os dados do arquivo resultData.json 
        self.intervalo = intervalo #............ Intervalo em minutos, setado em 15 minutos.
        self.indice = indice #.................. Indice onde o app se encontra no vetor presente no arquivo results
        self.requisitos_selecionados = requisitos_selecionados
        self.resultados_gerados = None
        self.ms_selecionados = ms_selecionados
        self.arquivos = {
            'Pasta': pasta,
            'NomesArqs': [] 
        } #..................................... Aqui serão salvos as informações sobre os arquivos de salvamento.
        self.flag_gerado = 0 #.................. 0 = Não foi gerado, 1 = foi gerado.
        self.id = -1 # ......................... Id pq eu acho que vou precisar.


    def iniciar(self):
        self.abreArq()
        self.abrirArqDados()
        self.vaiProCaso()
        self.montar()
        self.salvarArqGestao()
        print(f"Salvo em: ", self.arquivos['Pasta']) 

    def abreArq(self):
        # Função que abre o arquivo result e transfere seus dados aos atributos da classe
        self.name_app = self.result["App"]
        self.microsservices = [ i for i in self.result['Resultados'] ] # For que coloca os Micro
    
    def dadosIniciais(self, indice, nome):
        return {
            "NameFile": nome,
            "NameAPP": self.name_app,
            "NameOfMicroService": self.microsservices[indice]['MS'],
            "Provider": self.microsservices[indice]['Prvd'],
            "Availability": self.microsservices[indice]['Ava'],
            "Cost": self.microsservices[indice]['Cost'],
            "ResponseTime": self.microsservices[indice]['RT'],
            "Interval": self.intervalo,
            "Data_Inicial": str(self.date_initial),
            "Data_Final": str(self.date_final),
            "Monitoring": [] 
        }

    def verificaPasta(self) -> bool:
        if os.path.exists(os.path.join(self.arquivos["Pasta"], str(self.id))) == False:
            os.makedirs( os.path.join(self.arquivos["Pasta"], str(self.id) ) )
            return False
        else:
            return True # Uma pasta com este ID já foi criado.

    def abrirPasta(self):
        self.id = random.randint(0, 1000)
        while(self.verificaPasta() == True):
            self.id = random.randint(0, 1000)
        self.arquivos['Pasta'] = os.path.join(self.arquivos['Pasta'], str(self.id))
            

    def abrirArqDados(self):
        self.abrirPasta()
        for indice, i in enumerate(self.microsservices):
            nome = (f'{self.name_app}_MS{i["MS"]}_P{i["Prvd"]}.json')
            if len(self.arquivos['Pasta']) > 0:
                nome2 = os.path.join(self.arquivos["Pasta"], nome)
                #nome = (f'{self.arquivos["Pasta"]}/{nome}')
            arq = open(nome2, 'w')
            arq.close()
            aux = self.dadosIniciais(indice, nome)
            saveFinalFile(nome2, aux)
            self.arquivos['NomesArqs'].append(nome2)

    def vaiProCaso(self):
        # Função que verifica qual caso é o selecionado e em seguida chama a função referente ao caso.
        if self.case < 4:
            self.casos_basicos()
        elif self.case == 4:
            self.selecionarRequisito()
        elif self.case == 5:
            self.selecionarMicroServ()

    def casos_basicos(self):
        # Função chama as funções para a definição de limites.
        for i in range(len(self.microsservices)):
            if self.case == 1:
                # Melhor Caso
                self.microsservices[i]['limitesSel'] = self.melhorCaso(i)
            
            elif self.case == 2:
                # Pior Caso
                self.microsservices[i]['limitesSel'] = self.piorCaso(i)

            elif self.case == 3:
                # Aleatório
                self.microsservices[i]['limitesSel'] = self.aleatorio(i)

    def melhorCaso(self, indice):
        # Seleciona os limites referentes ao melhor caso.
        limites = {
            'Availability': {
                'Inicio': float(self.microsservices[indice]['Ava']), 
                'Final': 1.0
            },
            
            'Cost': {
                'Inicio': 0.001, 
                'Final': float(self.microsservices[indice]['Cost'])
            },
            
            'ResponseTime': {
                'Inicio': 0.001, 
                'Final': float(self.microsservices[indice]['RT'])
            }
        }

        return limites

    def piorCaso(self, indice):
        # Seleciona os limites referentes ao pior caso.
        limites = {
            'Availability': {
                'Inicio': 0.0, 
                'Final': float(self.microsservices[indice]['Ava'])
            },
            'Cost': {
                'Inicio': float(self.microsservices[indice]['Cost']), 
                'Final': float(self.microsservices[indice]['Cost']) * 3
            },
            'ResponseTime': {
                'Inicio': float(self.microsservices[indice]['RT']), 
                'Final': float(self.microsservices[indice]['RT']) * 3
            }
        }
        return limites

    def aleatorio(self, indice):
        # Seleciona os limites referentes ao pior caso.
        limites = {
            'Availability': {
                'Inicio': 0.0, 
                'Final': 1.0
            },
            'Cost': {
                'Inicio': 0.0, 
                'Final': float(self.microsservices[indice]['Cost']) * 2
            },
            'ResponseTime': {
                'Inicio': 0.0, 
                'Final': float(self.microsservices[indice]['RT']) * 2
            }
        }
        return limites

    def selecionarRequisito(self):
        self.casos_requisitos(self.requisitos_selecionados)

    def casos_requisitos(self, selecionados):
        for indice, i in enumerate(self.microsservices):
            i['limitesSel'] = self.requisito(selecionados, indice)
    
    def requisito(self, selecionados, indice):
        limite = {}

        if( 1 in selecionados ):
            limite['Availability'] = {
                'Inicio':  0.0,
                'Final': float(self.microsservices[indice]['Ava'])
            }
        else:
            limite['Availability'] = {
                'Inicio': float(self.microsservices[indice]['Ava']),
                'Final': 1.0
            }

        if ( 2 in selecionados ):
            limite['Cost'] = {
                'Inicio': float(self.microsservices[indice]['Cost']), 
                'Final': float(self.microsservices[indice]['Cost']) * 3
            }
        else:
            limite['Cost'] = {
                'Inicio': 0.0001, 
                'Final': float(self.microsservices[indice]['Cost'])
            }
        
        if( 3 in selecionados ):
            limite['ResponseTime'] = {
                'Inicio': float(self.microsservices[indice]['RT']), 
                'Final': float(self.microsservices[indice]['RT']) * 3
            }
        else:
            limite['ResponseTime'] = {
                'Inicio': 0.001, 
                'Final': float(self.microsservices[indice]['RT'])
            }
        
        return limite

    def selecionarMicroServ(self):
        self.casos_microsservico(self.ms_selecionados)

    def casos_microsservico(self, selecionados):
        for indice, i in enumerate(self.microsservices):
            i['limitesSel'] = self.limitarMS(selecionados, indice, i)

    def limitarMS(self, selecionados, indice, ms):
        if ms['MS'] in selecionados:
            retorno = self.piorCaso(indice)
        else:
            retorno = self.melhorCaso(indice)
        return retorno
    

    def montar(self):
        if self.flag_gerado == 0:
            for indice, i in enumerate(self.microsservices):
                aux = copy.deepcopy(self.date_initial)
                nome = self.arquivos['NomesArqs'][indice]
                arq = loadFile(nome)
                if arq != None:
                    while( compareDate(aux, self.date_final) == False ):
                        arq = self.gerar(arq, i, aux)
                        aux = avancaTempo(aux, self.intervalo)
                    saveFinalFile(nome, lido=arq)
            self.flag_gerado = 1
        

    def gerar(self, arq, ms, data):
        # arq: arquivo json
        # ms: microsserviço
        # data: data atual
        ava = random.uniform( 
            ms['limitesSel']['Availability']['Inicio'], 
            ms['limitesSel']['Availability']['Final'] )

        cost = random.uniform(
            ms['limitesSel']['Cost']['Inicio'], 
            ms['limitesSel']['Cost']['Final'] )

        rt = random.uniform(
            ms['limitesSel']['ResponseTime']['Inicio'], 
            ms['limitesSel']['ResponseTime']['Final'] )

        ava = round(ava, 2)
        cost = round(cost, 2)
        rt = round(rt, 2)

        arq['Monitoring'].append(
            {
                'Date': str(data.date()),
                'Time': str(data.time()),
                'Availability': ava,
                'Cost': cost,
                'ResponseTime': rt
            }
        )
        return arq

    def ziparArq(self):
        z = zipfile.ZipFile(os.path.join(self.arquivos['Pasta'], 'final.zip'), 'w', zipfile.ZIP_DEFLATED)
        for i in self.arquivos['NomesArqs']:
            z.write(i, os.path.basename(i))
        z.close()


    def requisitoStr(self, num):
        requisitos = {1: "Availability", 2: "Cost", 3: "ResponseTime"}
        return requisitos[num]


    def geraCase(self):
        caso = {'numero': self.case}
        if self.case == 1:
            caso['titulo'] = 'Melhor Caso'
            caso['descricao'] = 'Taxa de disponibilidade, custo e tempo de resposta estão sendo atendidas por absolutamente todos os fornecedores'
        elif self.case == 2:
            caso['titulo'] = 'Pior Caso'
            caso['descricao'] = 'Taxa de disponibilidade, custo e tempo de resposta não estão sendo atendidas por absolutamente todos os fornecedores'
        elif self.case == 3:
            caso['titulo'] = 'Caso Aleatório'
            caso['descricao'] = 'Taxa de disponibilidade, custo e tempo de resposta estão sendo atendidas por absolutamente todos os fornecedores'
        elif self.case == 4:
            caso['titulo'] = 'Requisito(s) selecionados não atendidos'
            caso['descricao'] = '1 ou mais requisitos (disponibilidade, custo e tempo de resposta) que não serão atendidos'
            caso['selecionados'] = [self.requisitoStr(i) for i in self.requisitos_selecionados]
        elif self.case == 5:
            caso['titulo'] = 'Microsserviço(s) selecionados não atendidos'
            caso['descricao'] = '1 ou mais microsserviços que não serão atendidos'
            caso['selecionados'] = self.ms_selecionados
        return caso



    def salvarArqGestao(self):
        nome = os.path.join(self.arquivos['Pasta'], 'gestao.json')

        self.ziparArq()

        caso = self.geraCase()
        nomes = []

        for indice, i in enumerate(self.microsservices):
            nomes.append(f'{self.name_app}_MS{i["MS"]}_P{i["Prvd"]}.json')

        self.resultados_gerados = {
            'pasta': self.arquivos['Pasta'],
            'nomesArqs': nomes,
            'caso': caso
        }

        saveFinalFile(nameARQ=nome, lido=self.resultados_gerados)
