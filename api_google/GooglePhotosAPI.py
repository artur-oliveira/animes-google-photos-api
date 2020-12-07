import pickle
import os
import re
import requests
from time import sleep
from .Exception import *
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request

CLIENT_SECRET_FILE = 'client_secret.json'
API_SERVICE_NAME = 'photoslibrary'
API_VERSION = 'v1'
SCOPES = ['https://www.googleapis.com/auth/photoslibrary',
          'https://www.googleapis.com/auth/photoslibrary.edit.appcreateddata',
          'https://www.googleapis.com/auth/photoslibrary.sharing']


def _slugify3(text):
    new_text = ''
    text = text.strip()

    for char in text:
        if char.isalnum():
            new_text += char
        if char.isspace():
            new_text += '-'

    return new_text.lower()


def create_service():
    cred = None
    pickle_file = 'token.pickle'

    if os.path.exists(pickle_file):
        with open(pickle_file, 'rb') as token:
            cred = pickle.load(token)

    if not cred or not cred.valid:
        if cred and cred.expired and cred.refresh_token:
            cred.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            cred = flow.run_local_server()

        with open(pickle_file, 'wb') as token:
            pickle.dump(cred, token)

    try:
        serv = build(API_SERVICE_NAME, API_VERSION, credentials=cred)
        print(API_SERVICE_NAME, 'service created successfully')
        return serv
    except Exception as e:
        print(e)
    return None


class GooglePhotos:
    def __init__(self, debug=False):
        self.albums_list = []
        self.name_albums = []
        self.service = create_service()
        self.token = pickle.load(open('token.pickle', 'rb'))

        self.debug = debug

    def list_albuns(self):
        response = self.service.albums().list(
            pageSize=50,
            excludeNonAppCreatedData=False
        ).execute()

        self.albums_list = response.get('albums') if response.get('albums') is not None else []

        next_page_token = response.get('nextPageToken')

        while next_page_token:
            response = self.service.albums().list(
                pageSize=50,
                excludeNonAppCreatedData=False,
                pageToken=next_page_token
            ).execute()

            self.albums_list.extend(response.get('albums'))
            next_page_token = response.get('nextPageToken')

        self.__set_name_albuns()

    def list_albuns_from_array(self, array):
        self.albums_list = array
        self.__set_name_albuns()

    def __set_name_albuns(self):
        for item in self.albums_list:
            title = item.get('title')

            if title not in self.name_albums:
                self.name_albums.append(title)

    def get_album(self, name):
        self.__albums_not_empty()

        for item in self.albums_list:
            if item.get('title') == name:
                return item

        raise AlbumsNotFound

    def get_content_by_album(self, name_album):
        album_id = self.get_album(name_album).get('id')

        request_body = {
            'albumId': album_id,
            'pageSize': 25,
        }

        response = self.service.mediaItems().search(body=request_body).execute()

        list_media_items = response.get('mediaItems')
        next_page_token = response.get('nextPageToken')

        while next_page_token:
            request_body['pageToken'] = next_page_token

            response = self.service.mediaItems().search(body=request_body).execute()
            list_media_items.extend(response.get('mediaItems'))
            next_page_token = response.get('nextPageToken')

        return list_media_items

    def create_album(self, title, description=None):
        request_body = {
            'album': {'title': title}
        }
        request_enrichment = None

        if description is not None:
            request_enrichment = {
                'newEnrichmentItem': {
                    'textEnrichment': {
                        'text': description if len(description) <= 1000 else description[0:999]
                    }
                },
                'albumPosition': {
                    'position': 'LAST_IN_ALBUM'
                }
            }

        try:
            self.__title_already_in_album(title)
            self.__perform_create(request_body, request_enrichment)
            self.__debug('Album %s Criado' % title)
            return True
        except AlbumAlreadyExists:
            self.__debug('Album %s já existe' % title)
            return False

    def __perform_create(self, request_body, request_enrichment):
        response = self.service.albums().create(body=request_body).execute()

        if request_enrichment is not None:
            self.service.albums().addEnrichment(
                albumId=response.get('id'),
                body=request_enrichment
            ).execute()

        sleep(3.2)

    def upload(self, file_name, album_name, new_name=None):
        file = os.path.join(os.getcwd(), file_name)

        upload_url = 'https://photoslibrary.googleapis.com/v1/uploads'

        headers = {
            'Authorization': 'Bearer ' + self.token.token,
            'Content-type': 'application/octet-stream',
            'X-Goog-Upload-Protocol': 'raw',
            'X-Goog-Upload-File-Name': file_name if new_name is None else new_name
        }

        try:
            with open(file, 'rb') as f:
                response = requests.post(
                    upload_url,
                    headers=headers,
                    data=f.read()
                )

            self.__debug('UPLOAD DE %s FEITO COM SUCESSO' % file_name)

            if response.status_code == 200:
                request_body = {
                    'albumId': self.get_album(album_name).get('id'),
                    'newMediaItems': [{
                        'simpleMediaItem': {
                            'uploadToken': response.content.decode('utf-8')
                            }
                        }
                    ]
                }

                self.service.mediaItems().batchCreate(body=request_body).execute()
                return True
            else:
                return False
        except FileNotFoundError:
            pass

    def upload_cover_photo(self, name_album, url):
        from scraper.Scraper import AnimesScraper

        type_file = url.split('/')[-1].split('.')[-1]
        if type_file.startswith('images?'):
            type_file = 'jpeg'

        name = _slugify3(name_album)

        filename = 'cover-%s.%s' % (name, type_file)

        AnimesScraper.download(url, filename)
        self.upload(filename, name_album)

        sleep(2)

        try:
            os.remove(filename)
        except FileNotFoundError:
            pass

    def upload_episode(self, url, name_album):
        from scraper.Scraper import AnimesScraper
        filename = url.split('/')[-1]

        AnimesScraper.download(url)
        
        sucess = self.upload(filename, name_album)
        sleep(2)

        try:
            os.remove(filename)
            return sucess
        except FileNotFoundError:
            return sucess

    def __share(self, album_id):
        request_body = {
            'sharedAlbumOptions': {
                'isCollaborative': False,
                'isCommentable': True
            }
        }

        return self.service.albums().share(albumId=album_id, body=request_body).execute()

    def share_album(self, name_album):
        return self.__share(self.get_album(name_album).get('id'))

    def __debug(self, string):
        if self.debug:
            print(string)

    def __albums_not_empty(self):
        if len(self.albums_list) < 1:
            raise AlbumsIsEmpty

    def __title_already_in_album(self, title):
        if title in self.name_albums:
            raise AlbumAlreadyExists


if __name__ == '__main__':
    api = GooglePhotos()
    api.list_albuns()
