from abc import ABCMeta

from couchdbkit.ext.django.schema import DocumentMeta



class DocumentABCMeta(ABCMeta, DocumentMeta):
    """ Meta class must be subclass of all parents' meta classes """
    pass



def proxy_object(obj, **kwargs):
    """ Proxies an object to make it arbitrarily modifiable

    It is not possible to add arbitrary values to an couchdbkit Document,
    because all values have to fit the schema and have to be JSON serializable
    """

    class ProxyObject(object):
        """ Proxy for obj that can have properties of arbitrary type """

        def __init__(self, obj, **kwargs):
            self.obj = obj

            for key, val in kwargs.items():
                setattr(self, key, val)


        def __getattr__(self, attr):
            return getattr(self.obj, attr)


    cls = obj.__class__
    cls.register(ProxyObject)

    return ProxyObject(obj, **kwargs)
