#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Flask
from flask_restful import Resource, Api
from flask_httpauth import HTTPBasicAuth
from modules import capabilities
from modules import auth
from modules import establishment
from modules import inspection
from modules import document
from modules import user
from modules import public
from config import config as cfg
from flask_cors import CORS
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
api = Api(app)
CORS(app)
#cors = CORS(api, resources={r"/api/*": {"origins": "*"}})

api.add_resource(capabilities.Capabilities, '/api', endpoint='cide_api_capabilities',methods=['GET'])
api.add_resource(auth.Authentication, '/login', '/logout', endpoint='cide_api_authentication',methods=['GET'])
api.add_resource(establishment.Establishment, '/api/establishment', endpoint='cide_api_establishments', methods=['GET'])
api.add_resource(inspection.Coordinated, '/api/coordinated','/api/coordinated/<hashid>',endpoint='cide_api_coordinated_inspections', methods=['GET','POST','DELETE','PUT'])
api.add_resource(inspection.Specific, '/api/specific/<hashid>',endpoint='cide_api_specific_inspections', methods=['GET','POST'])
api.add_resource(inspection.SpecificTypes, '/api/specific/type',endpoint='cide_api_specific_inspections_types', methods=['GET'])
api.add_resource(inspection.Issue,'/api/issue/<hashid>', endpoint='cide_api_issues', methods=['GET','POST'])
api.add_resource(inspection.Score, '/api/score','/api/score/<hashid>', endpoint='cide_api_scores', methods=['GET','POST'])
api.add_resource(inspection.CriteriaScore, '/api/criterior/score', endpoint='cide_api_criteria_score', methods=['GET'])
api.add_resource(inspection.Criteria, '/api/criterior', endpoint='cide_api_criteria', methods=['GET'])

api.add_resource(inspection.Inspection, '/api/inspection/specific/delete',
                                        '/api/inspection/specific/issue/insert',
                                        endpoint='cide_api_inspections', methods=['GET','POST'])
api.add_resource(document.UploadDocument, '/api/document/upload', endpoint='cide_api_documents_upload', methods=['POST'])
api.add_resource(document.DownloadDocument, '/api/document/download', endpoint='cide_api_documents_downloads', methods=['GET'])
api.add_resource(document.DeleteDocument, '/api/document/delete', endpoint='cide_api_documents_delete',methods=['DELETE'])
api.add_resource(user.User, '/api/user','/api/user/update','/api/user/delete', endpoint='cide_api_users',methods=['GET','POST'])
api.add_resource(public.Public,'/api/public/reset-password', endpoint='cide_api_public', methods=['GET'])

@app.after_request
def after_request(response):
  response.headers.add('Access-Control-Allow-Origin', '*')
  response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
  response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
  return response

if __name__ == '__main__':
    app.run(debug=True,host=cfg.host,port=cfg.apiport)
