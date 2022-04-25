
class RequestError(Exception):

    def __init__(self, url, message):

        self.url = url
        self.message = message
        super().__init__(self.message)

    def __str__(self):

        return f'{self.message} ({self.url})'

class DatabaseError(Exception):

    def __init__(self, number, message='Multiple results instead of one.'):

        self.number = number
        self.message = message
        super().__init__(self.message)

    def __str__(self):

        return f'{self.message} ({self.number})'