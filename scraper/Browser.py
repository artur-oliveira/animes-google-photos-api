import mechanize
import http.cookiejar as cookielib


class Browser:
    """
    Classe usada para fazer requisições no animes vision, para utilizá-la, basta instanciar e rodar
    o método setup(), por exemplo br = Browser().setup()

    Variáveis de ambiente necessárias:
    EMAIL: Email para fazer login no Animes Vision
    PASSWORD: Senha de acesso
    """
    def __init__(self):
        """
        Construtor da classe
        OBS:
        os headers abaixo são necessários para fazer requisições de download, caso não houvesse isso iria dar erro 403
        """
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.87 '
                          'Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'identity;q=1, *;q=0',
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Sec - Fetch - Dest': 'video',
            'Sec - Fetch - Mode': 'no - cors',
            'Sec - Fetch - Site': 'same - site',
            'Referer': 'https://animesvision.biz/'}

    def __browser_conf(self):
        """
        Configuração do browser para que não seja tratado como um robô qualquer
        :return:
        """

        cookie = cookielib.CookieJar()
        browser = mechanize.Browser()

        browser.set_handle_robots(False)
        browser.set_handle_referer(False)
        browser.set_handle_refresh(True)
        browser.set_handle_redirect(True)
        browser.addheaders = [('User-Agent', self.headers.get('User-Agent')),
                              ('Accept', self.headers.get('Accept')),
                              ('Accept-Language', self.headers.get('Accept-Language')),
                              ('Accept-Encoding', self.headers.get('Accept-Encoding')),
                              ('Accept-Charset', self.headers.get('Accept-Charset')),
                              ('Connection', self.headers.get('Connection')),
                              ('Cache-Control', self.headers.get('Cache-Control')),
                              ('Referer', self.headers.get('Referer')),
                              ('Sec - Fetch - Dest', self.headers.get('Sec - Fetch - Dest')),
                              ('Sec - Fetch - Mode', self.headers.get('Sec - Fetch - Mode')),
                              ('Sec - Fetch - Site', self.headers.get('Sec - Fetch - Site'))]

        browser.set_cookiejar(cookie)

        return browser

    def setup(self):
        """
        Faz o login no site do animes vision (Necessário para pegar os links de download) e retorna o browser com login
        :return:
        """
        browser = self.__browser_conf()
        browser.open('http://animesvision.biz/login')

        browser.select_form(nr=0)
        browser.form['email'] = 'repolho.assado.ra@gmail.com'
        browser.form['password'] = 'Clashofclans00'
        browser.submit()

        return browser
