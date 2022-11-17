from spyne.application import Application
from spyne.decorator import srpc
from spyne.service import ServiceBase
from spyne.server.wsgi import WsgiApplication
from spyne.protocol.soap import Soap11
from spyne.model.complex import Iterable
from spyne.model.primitive import UnsignedInteger, Unicode, String, Integer, Mandatory, Float
from lxml import *
from wsgiref.simple_server import make_server
import time

class serveur_soap(ServiceBase):
    @srpc(Float, Float, _returns=Float)
    def calcul(distance, autonomie): 
        nbr_trajet = distance // autonomie
        return nbr_trajet

app = Application([serveur_soap], 
                  'spyne.examples.hello.http', 
                  in_protocol=Soap11(validator='lxml'),
                  out_protocol=Soap11(),
                  )
wsgi_app = WsgiApplication(app)

if __name__ == '__main__':
    server = make_server('127.0.0.1', 3000, wsgi_app)
    server.serve_forever()