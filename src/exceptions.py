class IconButtonException(Exception):
    def __init__(self, message=None):
        self.message = message

    def __str__(self):
        return self.message


class NullRoot(Exception):
    def __init__(self, message=None):
        self.message = message

    def __str__(self):
        return self.message


class TextRectException(Exception):
    def __init__(self, message=None):
        self.message = message

    def __str__(self):
        return self.message
