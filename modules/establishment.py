import json
from flask_restful import Resource
from flask import request, Response,g,jsonify
from flask_httpauth import HTTPBasicAuth
from modules import auth as authentication
auth = HTTPBasicAuth()
class Establishment(Resource):
    @auth.verify_password
    def verify_pw(username, password):
        print(username)
        print(password)
        authenticate = authentication.Authentication()
        user = authenticate.verify_user_pass(username, password)
        print(user)
        if not user:
            return False
        #g.user = user
        return True

    @auth.login_required
    def get(self):
        query = []
        where = []
        for argument in request.args:
            query.append({argument:request.args.get(argument)})
            subquery = ("%s LIKE '%s' AND " % (argument,request.args.get(argument)))
            where.append(subquery)
        input_dict = json.load(open('Data/establishments.json'))
        sql_where = ''.join(where).rstrip(" AND ")
        if query:
            if "name" in ''.join(map(str,query)) and "oib" not in ''.join(map(str,query)):
                output_dict = [x for x in input_dict if query[0]['name'] in x['name']]
            elif "oib" in ''.join(map(str,query)) and "name" not in ''.join(map(str,query)):
                output_dict = [x for x in input_dict if str(query[0]['oib']) in str(x['oib'])]
            elif "oib" in ''.join(map(str,query)) and "name" in ''.join(map(str,query)):
                output_dict = [x for x in input_dict if str(query[1]['oib']) in str(x['oib']) and query[0]['name'] in x['name']]
        else:
            output_dict = input_dict
        return Response(json.dumps(output_dict), mimetype='application/json')
        #return Response(open('Data/establishments.json'), mimetype='application/json')