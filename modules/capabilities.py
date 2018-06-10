from flask_restful import Resource
from flask import Response
import json
class Capabilities(Resource):
    def get(self):
        output_dict = json.load(open('data/swagger.json'))
        return Response(json.dumps(output_dict), mimetype='application/json')