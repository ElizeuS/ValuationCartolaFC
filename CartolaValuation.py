import sklearn.linear_model as lm
import pandas as pd
import requests


class CartolaValue():
    def __init__(self):
        self.played = 7
        self.minScore = 6
        self.home = 0.25
        self.away = 0.125
        self.round = 5
        self.rodada = self.get_homeAway()


    def requestData(self, url):
        response = requests.get(url)
        return response.json()

    ## Esta função organiza os dados dos jogadores em um dataframe.
    #
    #  @return dataframe
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


    ## Esta função é responsável por pegar o nome do clube do jogador pelo id_club.
    #
    #  @return JSON {'name': 'nome_clube'}
    def clubData(self, club_id, data):
        clubs = data['clubes']
        club = clubs[f"{club_id}"]
        print(club['nome'])
        return ({'name': club['nome']})

    ## Esta função é responsável por verificar a posição do jogador.
    #
    #  @return JSON {'posicao': 'posicao_jogador'}
    def getPosition(self, position_id, data):
        posicoes = data['posicoes']
        posi = posicoes[f"{position_id}"]
        return ({'posicao': posi["nome"]})

    ## Esta função é responsável por calcular uma possível variação de preço do jogador, com base no preço e média do jogador.
    #
    #  @return dataframe
    def regVlorizacao(self, data):
        linear = lm.LinearRegression()

        played = data[data.jogos > 0]

        x = pd.DataFrame(columns=['preco', 'pontuacao'])
        y = played['variacao']
        x['preco'] = played['preco'] - played['variacao']
        x['pontuacao'] = played['pontos_ult']


        linear.fit(x, y)
        tabela = pd.DataFrame(columns=['clube', 'apelido', 'posicao', 'pontos_ult',
                                       'media', 'preco', 'variacao', 'predict', 'fator_casa', 'fator_tabela'])
        print(linear.predict([[10.65, 0.8]]))
        for i in range(len(data['preco'])):
            fatores = self.home_away(data.iloc[i]['clube_id'])

            tabela = tabela.append({'clube': data.iloc[i]['club_name'], 'apelido': data.iloc[i]['apelido'],
                                    'posicao': data.iloc[i]['posicao'], 'pontos_ult': data.iloc[i]['pontos_ult'], 'media': data.iloc[i]['media'], 'preco': data.iloc[i]['preco'],
                                    'variacao': data.iloc[i]['variacao'], 'predict': linear.predict([[data.iloc[i]['preco'], data.iloc[i]['media']]]), 'fator_casa': fatores['fator_casa'],
                                    'fator_tabela': fatores['fator_tabela']}, ignore_index=True)
        return tabela

    ## Esta função é responsável por normalizar um conjunto de dados, deixando-os no intervalo (0 - 1).
    #
    #  @return float (valor_normalizado)
    def normalizer(self, value, max, min):
        return ((value-min) / (max-min))

    ## Esta função é responsável pverificar na rodada quais times jogarão em casa ou fora.
    #
    #  @return  dataframe
    def get_homeAway(self):
        url = "https://api.cartolafc.globo.com/partidas/{}".format(str(self.round))
        res = self.requestData(url)
        rodada = pd.DataFrame(
            columns=['casa_id', 'fora_id', 'casa_posicao', 'fora_posicao'])

        for par in res['partidas']:
            rodada = rodada.append({'casa_id': par['clube_casa_id'], 'fora_id': par['clube_visitante_id'],
                                    'casa_posicao': par['clube_casa_posicao'], 'fora_posicao': par['clube_visitante_posicao']}, ignore_index=True)
        return rodada

    ## Esta função é responsável por atribuir pesos aos jogos dos times como mandantes ou visitantes, como também à posição do clube na tabela.
    #
    #  @return JSON
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


    ## Esta função é responsável por organizar os dados antes da exibição, acalculando o fator predominante para a escolha dos jogadores.
    def arranjeData(self, data):
        max_variacao = data['variacao'].max()
        min_variacao = data['variacao'].min()
        max_media = data['media'].max()
        min_media = data['media'].min()

        data['calc'] = ((data['media'])
                        + (self.normalizer(data['variacao'],
                                           max_variacao, min_variacao))
                        + (data['fator_casa'] * 2) + (data['fator_tabela'] * 4))/8

        self.print_values(data, self.round)


    ## Esta função é responsável por exibir separar os dados pela posição dos jgadores e e filtrar pelas regras determinadas.
    #
    #  @return dataframe
    def print_values(self, data, round):
        #new_data = self.third_round(data)
        new_data = self.other_rounds(data)
        tec = new_data[new_data['posicao'] == "Técnico"]
        gol = new_data[new_data['posicao'] == "Goleiro"]
        zag = new_data[new_data['posicao'] == "Zagueiro"]
        lat = new_data[new_data['posicao'] == "Lateral"]
        mei = new_data[new_data['posicao'] == "Meia"]
        ata = new_data[new_data['posicao'] == "Atacante"]

        if round == 3:

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
            print(ata.sort_values(by='min_pt', ascending=True))
        else:
            tec = tec.loc[(tec['media'] > 3 ) & (tec['calc'] > 0.8)]
            gol = gol.loc[(gol['media'] > 3 ) & (gol['calc'] > 0.8)]
            zag = zag.loc[(zag['media'] > 3 ) & (zag['calc'] > 0.8)]
            lat = lat.loc[(lat['media'] > 3 ) & (lat['calc'] > 0.8)]
            mei = mei.loc[(mei['media'] > 3 ) & (mei['calc'] > 0.8)]
            ata = ata.loc[(ata['media'] > 3 ) & (ata['calc'] > 0.8)]

            print(tec.sort_values(by=['media', 'pontos_ult'], ascending=[False, True]).head(10))
            print(gol.sort_values(by=['media', 'pontos_ult'], ascending=[False, True]).head(10))
            print(zag.sort_values(by=['media', 'pontos_ult'], ascending=[False, True]).head(10))
            print(lat.sort_values(by=['media', 'pontos_ult'], ascending=[False, True]).head(10))
            print(mei.sort_values(by=['media', 'pontos_ult'], ascending=[False, True]).head(10))
            print(ata.sort_values(by=['media', 'pontos_ult'], ascending=[False, True]).head(10))


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

    def other_rounds(self, data):
        data = data[(data.media > 0 )]
        #data = data[(data.pontos_ult != 0 ) | (data.variacao !=0)]
        #data = data.sort_values(by='pontos_ult', ascending=True).head(100)
        return data


c = CartolaValue()
reg = c.playersData()
prev = c.regVlorizacao(reg)
c.arranjeData(prev)
