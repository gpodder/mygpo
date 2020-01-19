class UsernameConverter:
    regex = r'[\w.+-]+'

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value


class ClientUIDConverter:
    regex = r'[\w.-]+'

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value
