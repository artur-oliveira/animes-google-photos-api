import re
import requests
from tqdm import tqdm
from .Browser import Browser
from mechanize.polyglot import HTTPError, URLError
from .Exception import PathIsEmpty, NotHasStreamLinks
from bs4 import BeautifulSoup


class AnimesScraper:
    """
    Classe para fazer a raspagem dos links de stream (download não implementado por causa de um bloqueio no servidor
    deles)
    """
    def __init__(self, debug=False, start=1, finish=1):
        """
        Construtor da classe, não é necessário passar nenhum argumento, mas poderá modificar o inicio e o final da pesqu
        isa no site
        OBS:
        modifique a variável _DEBUG abaixo para False caso deseje desativar as mensagens de log na tela
        """
        self._browser = Browser().setup()
        self.path = []
        self._start = start
        self._finish = finish
        self._DEBUG = debug
        self._ANIMES_VISION = 'http://animesvision.biz'
        self._PATTERN_RECENTLY = '/ultimas-adicionadas?page='

    def run(self):
        """
        Função principal que percorre um conjunto de páginas (Caso tenha instanciado a classe sem passar nada, irá ser p
        esquisada apenas os animes contidos na página 'http://animesvision.biz/ultimas-adicionadas?page=1') e adicionar
        os dados em um array
        :return:
        """
        self.set_animes()
        self.set_download_links()
        self.__separate_quality()

    def run_all_site(self, start=1, finish=136):
        """
        Faz a mesma coisa que a função principal, mas que percorre o site inteiro (Com base que o fim é na página 131)
        :param start: Início da pesquisa
        :param finish: Fim da pesquisa
        :return:
        """
        self._start = start
        self._finish = finish
        self.run()

    def set_animes(self):
        """
        Função pública que adiciona os "paths" na forma de dicionário, na variável self.path
        :return:
        """
        self.__scan_all_paths()

    def set_stream_links(self):
        """
        Função pública que coloca os links de stream em seu determinado dicionário contido na variável self.path
        :return:
        """
        self.__path_is_empty()
        self.__set_stream_links()

    def set_download_links(self):
        """
        Função pública que coloca os links de stream em seu determinado dicionário contido na variável self.path
        :return:
        """
        self.__path_is_empty()
        self.__set_download_links()

    def __separate_quality(self):
        new_path = []

        for item in self.path:
            download_links = item.get('download')
            if download_links:
                if download_links.get('480p'):
                    new_path.append(self.__change_quality(item, '480p'))
                if download_links.get('720p'):
                    new_path.append(self.__change_quality(item, '720p'))
                if download_links.get('1080p'):
                    new_path.append(self.__change_quality(item, '1080p'))

        del self.path

        self.path = new_path

    @staticmethod
    def __change_quality(item, quality):
        return {'title': item.get('title') + ' - %s' % quality,
                'description': item.get('description'),
                'img': item.get('img'),
                'episodes': item.get('download').get(quality)}


    def __get_list_animes(self, pattern, string):
        """
        Pesquisa a lista de animes de uma determinado página e salva no array self.path
        :param pattern: determinação de onde deve ser pesquisado, caso não seja modificado, irá ser utilizado o "ultimas
        -adicionadas?page="
        :param string: identificador da página Ex: 1, 2, 3 (o nome é string porque é uma string kek)
        :return:
        """
        url = self._ANIMES_VISION + pattern + string
        soup = self.__get_soup(url)

        anchor = soup.find_all('a', {'class': 'thumb'})

        for item in anchor:
            dict_ = {'url': item.get('href'), 'img': item.find('img').get('src'), 'title': item.get('title')}
            self.path.append(dict_)

    def __scan_all_paths(self):
        """
        Pesquisa a lista de animes de um determinado intervalo de páginas o Padrão é 1-1 (Pesquisa apenas na primeira pá
        gina)
        :param start: Inicio da paginação
        :param finish: Fim da paginação
        :return:
        """
        for i in range(self._start, self._finish + 1):
            url = self._ANIMES_VISION + self._PATTERN_RECENTLY + str(i)
            self.__get_list_animes(self._PATTERN_RECENTLY, str(i))

            self.__debug('Pesquisando em', url)

    def __get_links_from_path(self, dict_, magic_number):
        """
        Esta função pega os links de stream (ou download), e adiciona numa lista
        :param dict_: Dicionário que está contido no array self.path
        :param magic_number: 1 para retornar os links de stream, qualquer outro para retornar os links de download
        :return: array contendo os links de stream ou download
        """
        self.__debug('Analisando', dict_.get('url'))
        links_stream = []
        links_download = []

        url = self._ANIMES_VISION + dict_.get('url')
        soup = self.__get_soup(url)
        meta = soup.find('meta', property='og:description')
        if meta is not None:
            dict_['description'] = meta.get('content')

        episodes_div = soup.find('div', id='episodes-list')
        anchor_tag = episodes_div.find_all('a', class_='btn btn-sm btn-go2')

        for a in anchor_tag:
            if re.search('download', a['onclick']) is None:
                links_stream.append(self.__get_onclick(a['onclick']))
            else:
                links_download.append(self.__get_onclick(a['onclick']))

        return links_stream if magic_number == 1 else links_download

    def __set_stream_links(self):
        """
        Função que serve para setar os links diretos de stream no array self.path
        :return:
        """
        self.path.reverse()
        count = 1
        for item in self.path:
            self.__set_stream_links_base(item)
            self.__debug('Restam %d' % (len(self.path) - count), ' Animes')
            count += 1

    def __set_download_links(self):
        """
        Função que serve para setar os links diretos de stream no array self.path
        :return:
        """
        self.path.reverse()
        count = 1
        for item in self.path:
            self.__set_download_links_base(item)
            self.__debug('Restam %d' % (len(self.path) - count), ' Animes')
            count += 1

    def __set_download_links_base(self, document, links=None, count=None):
        """
        Dado um certo dicionario (especificamente aqueles que estão contidos no array self.path) serão pesquisados os
        links diretos de stream e setados no mesmo dicionário dentro do self.path
        :param document: Dicionário contido dentro do self.path
        :param links: argumento opcional que especifica os links a serem pesquisados
        :param count: altera o contador inicial
        :return:
        """
        dict_ = {'480p': {}, '720p': {}, '1080p': {}}

        if count is None:
            count = 1
        if links is None:
            links = self.__get_links_from_path(document, 0)

        for episode in links:
            ep = self.__get_download_from_url(episode)

            if ep is not None:
                if ep.get('480p'):
                    dict_['480p'][str(count)] = ep.get('480p')
                if ep.get('720p'):
                    dict_['720p'][str(count)] = ep.get('720p')
                if ep.get('1080p'):
                    dict_['1080p'][str(count)] = ep.get('1080p')
                count += 1

            self.__debug('Episodio ', '%d analisado' % (count - 1))

        document['download'] = dict_

    def __set_stream_links_base(self, document, links=None, count=None):
        """
        Dado um certo dicionario (especificamente aqueles que estão contidos no array self.path) serão pesquisados os
        links diretos de stream e setados no mesmo dicionário dentro do self.path
        :param document: Dicionário contido dentro do self.path
        :param links: argumento opcional que especifica os links a serem pesquisados
        :param count: altera o contador inicial
        :return:
        """
        dict_ = {'480p': {}, '720p': {}, '1080p': {}}

        if count is None:
            count = 1
        if links is None:
            links = self.__get_links_from_path(document, 1)

        for episode in links:
            ep = self.__get_stream_from_url(episode)

            if ep is not None:
                if ep.get('480p'):
                    dict_['480p'][str(count)] = ep.get('480p')
                if ep.get('720p'):
                    dict_['720p'][str(count)] = ep.get('720p')
                if ep.get('1080p'):
                    dict_['1080p'][str(count)] = ep.get('1080p')
                count += 1

        document['stream'] = dict_

    def __get_stream_from_url(self, url):
        """
        Esta função pega os links de stream de uma certa url e as adiciona em um dicionário separados por qualidade,
        também é verificada se existe uma qualidade melhor
        :param url: url a ser pesquisada
        :return: dicionario contendo as urls separadas por qualidade
        """
        soup = self.__get_soup(url)
        dict_ = {}
        if soup is not None:
            script = soup.find_all('script', type='application/javascript')
        else:
            return None

        for s in script:
            if s.contents:
                result = re.findall(r"(file:'(.*mp4[^',]*))", s.contents[0])
                if len(result) > 0:
                    link = result[0][1]
                    if '480p' in link:
                        dict_['480p'] = link
                    elif '720p' in link:
                        dict_['720p'] = link
                    else:
                        dict_['480p'] = link

        return self.__test_1080p(dict_)

    def __get_download_from_url(self, url):
        """
        Esta função pega os links de stream de uma certa url e as adiciona em um dicionário separados por qualidade,
        também é verificada se existe uma qualidade melhor
        :param url: url a ser pesquisada
        :return: dicionario contendo as urls separadas por qualidade
        """
        soup = self.__get_soup(url)
        dict_ = {}

        if soup is not None:
            anchor = soup.find_all('a', type='button')
        else:
            return None

        for a in anchor:
            link = a.get('href')
            if '480p' in link:
                dict_['480p'] = link
            elif '720p' in link:
                dict_['720p'] = link
            elif '1080p' in link:
                dict_['1080p'] = link

        return dict_

    def __test_1080p(self, dict_):
        """
        Esta função verifica se a qualidade 1080p está disponível para determinado anime
        :param dict_: Dicionário de qualidades para que seja feita a verificação
        :return:
        """
        url_480p = ''
        url_720p = ''

        if dict_.get('480p') is not None:
            url_480p = dict_.get('480p').replace('480p', '1080p')

        if dict_.get('720p') is not None:
            url_720p = dict_.get('720p').replace('720p', '1080p')

        if url_480p != '':
            if self.__found(url_480p):
                dict_['1080p'] = url_480p
                return dict_

        elif url_720p != '':
            if self.__found(url_720p):
                dict_['1080p'] = url_720p
                return dict_

        return dict_

    def __get_soup(self, url):
        """
        Apenas retorna a BeautifulSoup de uma determinada url
        :param url: url a ser pesquisada
        :return: classe BeautifulSoup
        """
        try:
            self._browser.open(url)
            response = self._browser.response()
            return BeautifulSoup(response.read(), 'html.parser')
        except HTTPError:
            self.__debug('Erro na URL:', url)

    def __debug(self, phrase, parameter):
        """
        Função que apenas serve para printar algo na tela (Há muitos casos de debug). Será necessário que seja trocada a
        variável self._DEBUG para False, se fossem utilizados vários prints, iria dar muito mais trabalho apagar todos
        :param phrase: qualquer coisa que voce deseje mostrar na tela
        :param parameter: qualquer coisa que voce deseje mostrar na tela
        :return:
        """
        if self._DEBUG:
            print('%s %s' % (phrase, parameter))

    def __path_is_empty(self):
        """
        Verifica se o array self.path está vazio, caso positivo irá ser lançada uma exceção
        :return:
        """
        if len(self.path) < 1:
            raise PathIsEmpty

    def __not_has_stream_links(self):
        """
        Verifica se os links de stream estão setados corretamente, caso contrário irá ser lançada uma exceção
        :return:
        """
        self.__path_is_empty()

        for item in self.path:
            if item.get('stream') is None:
                raise NotHasStreamLinks

    def __found(self, url):
        """
        Verifica se o código da requisição foi 200, caso haja alguma exceção irá ser tratado como outro valor
        :param url: url a ser pesquisada
        :return: retorna True caso o código da requisição for 200, e False em qualquer outra possibilidade
        """
        try:
            response = self._browser.open(url)
            return response.code == 200
        except HTTPError as e:
            return False
        except URLError as e:
            return False

    @staticmethod
    def __get_onclick(string):
        """
        Retorna o link contido dentro de um "window.open()"
        :param string: string a ser pesquisada
        :return: retorna uma string contendo o que está dentro de um onclick
        """
        return re.findall(r"'(.*?)'", string)[0]

    @staticmethod
    def download(url, name=None):
        """
        Função utilizada para fazer download de um certo link do animes vision sem o erro 403
        :param url: url de download direto
        :param name: nome do arquivo a ser salvo
        :return:
        """
        import os

        if name is None:
            name = url.split('/')[-1]

        if not name.endswith('mp4'):

            r = requests.get(url, headers=Browser().headers)

            if r.status_code == 200:
                with open(name, 'wb') as file:
                    file.write(r.content)
                print('Download completo de %s' % url)

            if r.status_code == 404:
                print('Url invalida')

        else:
            r = requests.get(url, headers=Browser().headers, stream=True, verify=False)
            length = r.headers.get('content-length')
            try:
                length = int(length)
            except TypeError:
                print('Falha no download')
                return

            with open(name, 'wb') as file:
                for data in tqdm(iterable=r.iter_content(chunk_size=1024), total=(length / 1024) + 1, unit='KB'):
                    file.write(data)

            if int(os.stat(name).st_size) != length:
                AnimesScraper.download(url, name)

            print('Download completo')


if __name__ == '__main__':
    print('KEK')
