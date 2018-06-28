from flask_restful import Resource
from flask import request,g,make_response
from flask_httpauth import HTTPBasicAuth
import requests,json,urllib
from werkzeug.security import generate_password_hash, check_password_hash


auth = HTTPBasicAuth()

class Authentication(Resource):
    def __init__(self):
        self.authservice = 'http://pproo.azo.hr/bifisic/services/httpbasicauth/auth'
    def get(self):
        if "login" in request.url:
            authtype = "LOGIN"
        elif "logout" in request.url:
            logged_user = auth.username()
            self.verify_user_pass('noone','nothing')
            return "User %s logged out!" % logged_user
        else:
            authtype = "REGISTER"
        '''
        if authtype == 'LOGIN' or authtype == 'LOGOUT':
            user = request.args.get('user')
            password = request.args.get('password')
        '''
    def verify_user_pass(self,user,password):
        checkURL = self.authservice + '?user=' + user + '&password=' + password
        print(checkURL)
        responseData = json.loads(requests.get(checkURL).text)
        if responseData == '401 Unauthorized':
            return False
        else:
            return responseData['name'],responseData['roles']


