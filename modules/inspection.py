import json
from flask_restful import Resource
from flask import request, Response,g,jsonify
from flask_httpauth import HTTPBasicAuth
from modules import auth as authentication
auth = HTTPBasicAuth()
class Inspection(Resource):
    @auth.verify_password
    def verify_pw(username, password):
        print(username)
        print(password)
        authenticate = authentication.Authentication()
        user = authenticate.verify_user_pass(username, password)
        print(user)
        if not user:
            return False
        g.user = user
        return True

    def get(self,estab_id=False):
        input_dict = json.load(open('data/coordinated_inspections.json'))
        if estab_id:
            output_dict = [x for x in input_dict if x['establishment_ref'] == int(estab_id)]
        else:
            output_dict = input_dict
        return Response(json.dumps(output_dict), mimetype='application/json')


