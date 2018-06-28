from flask_restful import Resource
from flask import Response,g
from flask_httpauth import HTTPBasicAuth
import json
from modules import auth as authentication
from modules import person as personcheck
auth = HTTPBasicAuth()
class Capabilities(Resource):
    @auth.verify_password
    def verify_pw(username, password):
        print(username)
        print(password)
        authenticate = authentication.Authentication()
        user = authenticate.verify_user_pass(username, password)
        if not user:
            return False
        g.user = user[0]
        # CHECK IF USER AND ROLES EXIST IN cide_person and cide_role tables, if not create one if yes return OK
        check = personcheck.Person()
        person = check.checkLoggedUser(user)
        print("CHECK LOGGED USER STATUS: %s" % person)
        return True
    @auth.login_required
    def get(self):
        output_dict = json.load(open('data/swagger.json'))
        return Response(json.dumps(output_dict,ensure_ascii=False), mimetype='application/json')