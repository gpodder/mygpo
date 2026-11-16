from django.urls import register_converter

from mygpo.users import converters
from mygpo.usersettings.converters import ScopeConverter


register_converter(converters.ClientUIDConverter, "client-uid")
register_converter(converters.UsernameConverter, "username")
register_converter(ScopeConverter, "scope")
