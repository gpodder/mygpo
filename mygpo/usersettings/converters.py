class ScopeConverter:
    regex = 'account|device|podcast|episode'

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value
