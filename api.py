#!/usr/bin/env python
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
api.add_resource(inspection.Inspection, '/api/inspection/',
                                        '/api/inspection/<hashid>',
                                        '/api/inspection/specific/<hashid>',
                                        '/api/inspection/insert',
                                        '/api/inspection/update',
                                        '/api/inspection/specific/type',
                                        '/api/inspection/specific/type/insert',
                                        '/api/inspection/specific/criterior',
                                        '/api/inspection/specific/criterior/insert',
                                        '/api/inspection/specific/issue/<hashid>',
                                        '/api/inspection/specific/criterior/score')

if __name__ == '__main__':
    app.run(debug=True,host=cfg.host,port=cfg.apiport)
