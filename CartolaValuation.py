from typing import TYPE_CHECKING
import numpy as np
import matplotlib.pyplot as plt
import sklearn.linear_model as lm
import pandas as pd
import requests

class CartolaValue():
    def __init__(self):
        self.played = 7
        self.minScore = 5

    def requestData(self, url):
        response =  requests.get(url)
        return response.json()

    def playersData(self):
        url = 'https://api.cartolafc.globo.com/atletas/mercado'
        res = self.requestData(url)
        players = res['atletas']
        data = pd.DataFrame(columns=['apelido','clube_id', 'club_name','posicao_id', 'posicao' ,'preco','media', 'variacao', 'jogos'])
        for at in players:
            if at['status_id'] == self.played:
                clubName = self.clubData(at['clube_id'], res)
                position = self.getPosition(at['posicao_id'], res)
                data = data.append({'apelido': at['apelido'], 'clube_id': at['clube_id'], 'club_name': clubName['name'], 'posicao_id': at['posicao_id'],
                           'posicao': position['posicao'], 'preco': at['preco_num'], 'media': at['media_num'],'variacao': at['variacao_num'],'jogos': at['jogos_num'] }, ignore_index=True)
        print(data)
        return data

    def clubData(self, club_id, data):
        clubs = data['clubes']
        club = clubs[f"{club_id}"]
        print(club['nome'])
        return ({'name': club['nome']})

    def getPosition(self, position_id, data):
        posicoes = data['posicoes']
        posi = posicoes[f"{position_id}"]
        return ({'posicao': posi["nome"]})

    def regVlorizacao(self, data):
        linear = lm.LinearRegression()

        played = data[data.jogos > 0]

        x = pd.DataFrame(columns=['preco', 'pontuacao'])
        y = played['variacao']
        x['preco'] = played['preco'] - played['variacao']
        x['pontuacao'] = played['media']

        linear.fit(x, y)
        print(played)
        tabela = pd.DataFrame(columns=['clube', 'apelido', 'posicao', 'media', 'preco', 'predict'])
        for i in range(len(data['preco'])):
            tabela = tabela.append({'clube': data.iloc[i]['club_name'], 'apelido': data.iloc[i]['apelido'],
                                   'posicao': data.iloc[i]['posicao'], 'media': data.iloc[i]['media'],'preco': data.iloc[i]['preco'],
                                   'predict': linear.predict([[data.iloc[i]['preco'], self.minScore]])}, ignore_index=True)

        return tabela

    def arranjeData(self, data):
        tec = data[data['posicao'] == "Técnico"]
        gol = data[data['posicao'] == "Goleiro"]
        zag = data[data['posicao'] == "Zagueiro"]
        lat = data[data['posicao'] == "Lateral"]
        mei = data[data['posicao'] == "Meia"]
        ata = data[data['posicao'] == "Atacante"]

        print(gol.sort_values(by='predict', ascending=False).head(10))
        print(zag.sort_values(by='predict', ascending=False).head(10))
        print(lat.sort_values(by='predict', ascending=False).head(10))
        print(mei.sort_values(by='predict', ascending=False).head(10))
        print(ata.sort_values(by='predict', ascending=False).head(10))
        return({ 'TEC': tec, 'GOL': gol, 'ZAG': zag, 'LAT': lat, 'MEI': mei, 'ATA': ata })

c = CartolaValue()
reg = c.playersData()
prev = c.regVlorizacao(reg)
c.arranjeData(prev)