import numpy as np
import matplotlib.pyplot as plt
import sklearn.linear_model as lm
import pandas as pd
import requests


class CartolaValue():
    def __init__(self):
        self.played = 7
        self.minScore = 6
        self.rodada = self.get_homeAway()
        self.home = 0.25
        self.away = 0.125

    def requestData(self, url):
        response = requests.get(url)
        return response.json()

    def playersData(self):
        url = 'https://api.cartolafc.globo.com/atletas/mercado'
        res = self.requestData(url)
        players = res['atletas']
        data = pd.DataFrame(columns=['apelido', 'clube_id', 'club_name', 'posicao_id',
                                     'posicao', 'preco', 'pontos_ult', 'media', 'variacao', 'jogos'])
        for at in players:
            if at['status_id'] == self.played:
                clubName = self.clubData(at['clube_id'], res)
                position = self.getPosition(at['posicao_id'], res)
                data = data.append({'apelido': at['apelido'], 'clube_id': at['clube_id'], 'club_name': clubName['name'], 'posicao_id': at['posicao_id'],
                                    'posicao': position['posicao'], 'preco': at['preco_num'], 'pontos_ult': at['pontos_num'], 'media': at['media_num'], 'variacao': at['variacao_num'], 'jogos': at['jogos_num']}, ignore_index=True)
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
        tabela = pd.DataFrame(columns=['clube', 'apelido', 'posicao', 'pontos_ult',
                                       'media', 'preco', 'variacao', 'predict', 'fator_casa', 'fator_tabela'])
        print(linear.predict([[17.68, 11.7]]))
        for i in range(len(data['preco'])):
            fatores = self.home_away(data.iloc[i]['clube_id'])

            tabela = tabela.append({'clube': data.iloc[i]['club_name'], 'apelido': data.iloc[i]['apelido'],
                                    'posicao': data.iloc[i]['posicao'], 'pontos_ult': data.iloc[i]['pontos_ult'], 'media': data.iloc[i]['media'], 'preco': data.iloc[i]['preco'],
                                    'variacao': data.iloc[i]['variacao'], 'predict': linear.predict([[data.iloc[i]['preco'], self.minScore]]), 'fator_casa': fatores['fator_casa'],
                                    'fator_tabela': fatores['fator_tabela']}, ignore_index=True)
        return tabela

    def normalizer(self, value, max, min):
        return ((value-min) / (max-min))

    def get_homeAway(self):
        url = 'https://api.cartolafc.globo.com/partidas/3'
        res = self.requestData(url)
        rodada = pd.DataFrame(
            columns=['casa_id', 'fora_id', 'casa_posicao', 'fora_posicao'])

        for par in res['partidas']:
            rodada = rodada.append({'casa_id': par['clube_casa_id'], 'fora_id': par['clube_visitante_id'],
                                    'casa_posicao': par['clube_casa_posicao'], 'fora_posicao': par['clube_visitante_posicao']}, ignore_index=True)
        return rodada

    def home_away(self, club_id):
        for val in range(len(self.rodada['casa_id'])):
            if self.rodada.iloc[val]['casa_id'] == club_id:
                ft = (self.normalizer(
                    self.rodada.iloc[val]['casa_posicao'], 1, 20))
                fc = 0.5
                return {'fator_casa': fc, 'fator_tabela': ft}
            elif self.rodada.iloc[val]['fora_id'] == club_id:
                ft = (self.normalizer(
                    self.rodada.iloc[val]['fora_posicao'], 1, 20))
                fc = 0.25
                return {'fator_casa': fc, 'fator_tabela': ft}

    def arranjeData(self, data):
        max_variacao = data['variacao'].max()
        min_variacao = data['variacao'].min()
        max_media = data['media'].max()
        min_media = data['media'].min()

        data['calc'] = ((self.normalizer(data['media'], max_media, min_media) * 5)
                        + (self.normalizer(data['variacao'],
                                           max_variacao, min_variacao))
                        + (data['fator_casa'] * 2) + (data['fator_tabela'] * 4))/12

        self.print_values(data)

    def print_values(self, data):
        new_data = self.third_round(data)
        tec = new_data[new_data['posicao'] == "Técnico"]
        gol = new_data[new_data['posicao'] == "Goleiro"]
        zag = new_data[new_data['posicao'] == "Zagueiro"]
        lat = new_data[new_data['posicao'] == "Lateral"]
        mei = new_data[new_data['posicao'] == "Meia"]
        ata = new_data[new_data['posicao'] == "Atacante"]

        tec = tec.loc[(tec['min_pt'] < 10 ) & (tec['calc'] > 0.4)]
        gol = gol.loc[(gol['min_pt'] < 10 ) & (gol['calc'] > 0.4)]
        zag = zag.loc[(zag['min_pt'] < 10 ) & (zag['calc'] > 0.4)]
        lat = lat.loc[(lat['min_pt'] < 10 ) & (lat['calc'] > 0.4)]
        mei = mei.loc[(mei['min_pt'] < 10 ) & (mei['calc'] > 0.4)]
        ata = ata.loc[(ata['min_pt'] < 10 ) & (ata['calc'] > 0.4)]

        print(tec.sort_values(by='min_pt', ascending=True))
        print(gol.sort_values(by='min_pt', ascending=True))
        print(zag.sort_values(by='min_pt', ascending=True))
        print(lat.sort_values(by='min_pt', ascending=True))
        print(mei.sort_values(by='min_pt', ascending=True))
        print(ata.sort_values(by='min_pt', ascending=True).head(15))


    def third_round(self, data):
        result = []
        for i in range(len(data["media"])):
            preco = data.iloc[i]['preco']
            media = data.iloc[i]["media"]
            if data.iloc[i]["media"] != 0:
                result.append((preco * 1.20) - media)
            else:
                result.append(preco*0.77)

        data["min_pt"] = result
        return data


c = CartolaValue()
reg = c.playersData()
prev = c.regVlorizacao(reg)
c.arranjeData(prev)
