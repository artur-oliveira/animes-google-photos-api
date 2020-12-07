class AlbumsIsEmpty(Exception):
    def __init__(self, message='The array "albums_list" is empty. You should fill it before with the "list_albuns" '
                               'method'):
        super().__init__(message)


class AlbumsNotFound(Exception):
    def __init__(self, message='The album given does not exists'):
        super().__init__(message)


class AlbumAlreadyExists(Exception):
    def __init__(self, message='The name of the album already exists in Google Photos'):
        super().__init__(message)
