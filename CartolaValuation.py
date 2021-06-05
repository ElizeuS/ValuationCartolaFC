import numpy as np
import matplotlib.pyplot as plt
import sklearn.linear_model as lm
import pandas as pd
import requests

class CartolaValue():
    def __init__(self):
        self.played = 7
        self.minScore = 5
        self.rodada = self.get_homeAway()
        self.home = 0.25
        self.away = 0.125

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
        tabela = pd.DataFrame(columns=['clube', 'apelido', 'posicao', 'media', 'preco', 'variacao', 'predict', 'fator_casa', 'fator_tabela'])
        for i in range(len(data['preco'])):
            fatores = self.home_away(data.iloc[i]['clube_id'])
            tabela = tabela.append({'clube': data.iloc[i]['club_name'], 'apelido': data.iloc[i]['apelido'],
                                   'posicao': data.iloc[i]['posicao'], 'media': data.iloc[i]['media'],'preco': data.iloc[i]['preco'],
                                   'variacao':data.iloc[i]['variacao'], 'predict': linear.predict([[data.iloc[i]['preco'], self.minScore]]), 'fator_casa': fatores['fator_casa'],
                                   'fator_tabela': fatores['fator_tabela']}, ignore_index=True)
        return tabela


    def normalizer(self, value, max, min):
        return ((value-min) / (max-min))

    def get_homeAway(self):
        url = 'https://api.cartolafc.globo.com/partidas/2'
        res = self.requestData(url)
        rodada = pd.DataFrame(columns=['casa_id', 'fora_id', 'casa_posicao', 'fora_posicao'])

        for par in res['partidas']:
            rodada = rodada.append({'casa_id': par['clube_casa_id'], 'fora_id': par['clube_visitante_id'],
                                'casa_posicao': par['clube_casa_posicao'], 'fora_posicao': par['clube_visitante_posicao']}, ignore_index=True)
        return rodada

    def home_away(self, club_id):
        for val in range(len(self.rodada['casa_id'])):
            if self.rodada.iloc[val]['casa_id'] == club_id:
                ft = (self.normalizer(self.rodada.iloc[val]['casa_posicao'], 1, 20))
                fc = 0.5
                return {'fator_casa': fc, 'fator_tabela': ft}
            elif self.rodada.iloc[val]['fora_id'] == club_id:
                ft = (self.normalizer(self.rodada.iloc[val]['fora_posicao'], 1, 20))
                fc = 0.25
                return {'fator_casa': fc, 'fator_tabela': ft}

    def arranjeData(self, data):
        data['calc'] = ((data['media'] *3 ) + (data['variacao'] * 2 ) + data['fator_casa'] + (data['fator_tabela'] * 3))/9

        tec = data[data['posicao'] == "Técnico"]
        gol = data[data['posicao'] == "Goleiro"]
        zag = data[data['posicao'] == "Zagueiro"]
        lat = data[data['posicao'] == "Lateral"]
        mei = data[data['posicao'] == "Meia"]
        ata = data[data['posicao'] == "Atacante"]

        print(tec.sort_values(by='calc', ascending=False).head(10))
        print(gol.sort_values(by='calc', ascending=False).head(10))
        print(zag.sort_values(by='calc', ascending=False).head(10))
        print(lat.sort_values(by='calc', ascending=False).head(10))
        print(mei.sort_values(by='calc', ascending=False).head(10))
        print(ata.sort_values(by='calc', ascending=False).head(10))
        return({ 'TEC': tec, 'GOL': gol, 'ZAG': zag, 'LAT': lat, 'MEI': mei, 'ATA': ata })


c = CartolaValue()
reg = c.playersData()
prev = c.regVlorizacao(reg)
c.arranjeData(prev)
c.home_away(286)