class UsernameConverter:
    regex = '[\w.+-]+'

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value


class ClientUIDConverter:
    regex = '[\w.-]+'

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value
