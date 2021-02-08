from scraper.Scraper import AnimesScraper
from api_google.GooglePhotosAPI import GooglePhotos
from utils import *

DATA_FILE_NAME = 'conf/data.json'
ALBUMS_FILE_NAME = 'conf/conf.json'
BLOCK_FILE_NAME = 'conf/block.json'
MISSING_FILE_NAME = 'conf/missing.json'
SHARE_URL_NAME = 'conf/share.json'


class Main:
    def __init__(self, debug=False, stream=True):
        self.arr = []
        self.block = []
        self.episodes_missing = {}
        self.share_url = {}
        self.debug = debug
        self.photos = GooglePhotos(debug)
        self.stream = stream

    def __setup(self):
        # DADOS DOS ANIMES
        if file_exists(DATA_FILE_NAME):
            self.arr = read_json(DATA_FILE_NAME)
        else:
            sc = AnimesScraper(self.debug, 114, 114)
            sc.run(self.stream)
            self.arr = [anime for anime in sc.path]

            write_json(self.arr, DATA_FILE_NAME)
            del sc

        # ALBUMS DO GOOGLE FOTOS
        if file_exists(ALBUMS_FILE_NAME):
            self.photos.list_albuns_from_array(read_json(ALBUMS_FILE_NAME))
        else:
            self.photos.list_albuns()
            write_json(self.photos.albums_list, ALBUMS_FILE_NAME)

        # ALBUMS COMPLETOS
        if file_exists(BLOCK_FILE_NAME):
            self.block = read_json(BLOCK_FILE_NAME)

        # EPISODIOS FALTANDO
        if file_exists(MISSING_FILE_NAME):
            self.episodes_missing = read_json(MISSING_FILE_NAME)

        if file_exists(SHARE_URL_NAME):
            self.share_url = read_json(SHARE_URL_NAME)

        self.__debug('Configuração inicial realizada')

    def run(self):
        self.__setup()

        while 1:
            count = -1
            try:
                for anime in self.arr:
                    count += 1
                    add_ep = 0
                    first_episode = True
                    name_album = anime.get('title')
                    img = anime.get('img')
                    episodes = anime.get('episodes')

                    if self.photos.create_album(name_album, anime.get('description')):
                        write_json(self.photos.albums_list, ALBUMS_FILE_NAME)

                    list_itens = self.photos.get_content_by_album(name_album)
                    episodes_albuns = len(list_itens) - 1 if list_itens is not None else 0
                    atual_episodes = len(episodes)

                    if name_album in self.block:
                        continue
                    if episodes_albuns == atual_episodes:
                        continue

                    if episodes_albuns == 0:
                        self.photos.upload_cover_photo(name_album, img)

                    for ep in episodes:
                        if self.episodes_missing.get(name_album):
                            add_ep = self.episodes_missing.get(name_album)
                        if first_episode:
                            first_episode = False
                            self.episodes_missing[name_album] = int(ep) - 1
                        if int(ep) > episodes_albuns + add_ep:
                            self.__debug('EPISODIO %s/%s DE %s' % (ep, atual_episodes + add_ep, name_album))
                            url = episodes.get(ep)
                            if self.photos.upload_episode(url, name_album):
                                continue
                            else:
                                self.photos = GooglePhotos(self.debug)
                                self.__setup()
                                self.photos.upload_episode(url, name_album)

                    if self.photos.get_album(name_album).get('shareInfo'):
                        self.share_url[name_album] = self.photos.get_album(name_album).get('shareInfo'). \
                            get('shareableUrl')
                    else:
                        self.share_url[name_album] = self.photos.share_album(name_album).get('shareInfo'). \
                            get('shareableUrl')

                    self.block.append(name_album)
                    write_json(self.block, BLOCK_FILE_NAME)
                    write_json(self.episodes_missing, MISSING_FILE_NAME)
                    write_json(self.share_url, SHARE_URL_NAME)

            except Exception as e:
                self.__debug(e)
                continue

    def __debug(self, msg):
        if self.debug:
            print(msg)


if __name__ == '__main__':
    """
    Se os downloads estiverem lentos, pode colocar stream=True, não é garantido que vá funcionar
    pois isso está diretamente ligado ao servidor do Animes Vision
    """
    Main(debug=True, stream=False).run()
