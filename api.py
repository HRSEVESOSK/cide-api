from flask import Flask
from flask_restful import Resource, Api
from flask_httpauth import HTTPBasicAuth
from modules import auth
from modules import establishment
from modules import inspection
app = Flask(__name__)
api = Api(app)


api.add_resource(auth.Authentication, '/login', '/logout')
api.add_resource(establishment.Establishment, '/establishment')
api.add_resource(inspection.Inspection,'/inspection/<estab_id>')


if __name__ == '__main__':
    app.run(debug=True)
