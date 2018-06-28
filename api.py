# -*- coding: utf-8 -*-
from flask import Flask
from flask_restful import Resource, Api
from flask_httpauth import HTTPBasicAuth
from modules import capabilities
from modules import auth
from modules import establishment
from modules import inspection
from config import config as cfg
app = Flask(__name__)
api = Api(app)

api.add_resource(capabilities.Capabilities, '/api')
api.add_resource(auth.Authentication, '/login', '/logout')
api.add_resource(establishment.Establishment, '/api/establishment')
api.add_resource(inspection.Inspection,'/api/inspection/','/api/inspection/<oib>','/api/inspection/insert','/api/inspection/update','/api/inspection/types')


if __name__ == '__main__':
    app.run(debug=True,host=cfg.host,port=cfg.port)
