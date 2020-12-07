class PathIsEmpty(Exception):
    def __init__(self, message='The array "path" is empty. You should fill it before with the "run" method or the '
                               '"set_animes" method'):
        super().__init__(message)


class NotHasStreamLinks(Exception):
    def __init__(self, message='The array "path" dont have stream links. You should fill it before with the "run" '
                               'method or the "set_stream_links" method'):
        super().__init__(message)
