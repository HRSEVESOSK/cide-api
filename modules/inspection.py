import json,datetime
from flask_restful import Resource
import urllib
from flask import request, Response,g,jsonify
from flask_httpauth import HTTPBasicAuth
from modules import auth as authentication
from modules import person as Person
import lib.pgsql as pgsql
auth = HTTPBasicAuth()
class Inspection(Resource):
    def __init__(self):
        self.connection =  pgsql.PGSql()
        self.personclass = Person.Person()
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
        # CHECK IF USER AND ROLES EXIST IN cide_person and cide_role tables, if not create one if yes return OK
        personClass =Person.Person()
        person = personClass.checkLoggedUser(user)
        print("CHECK LOGGED USER STATUS: %s" % person)
        return True

    @auth.login_required
    def get(self,oib=False):
        if not oib and not request.path.endswith("/types"):
            return Response('{"message":"missing oib filter"}', mimetype='application/json')
        if not oib and request.path.endswith("/types"):
            ## GET LIST OF SPEC INSP TYPES
            self.connection.connect()
            specinstypes = self.connection.query("SELECT des_inspection_type INSTYPE from cide_specific_inspection_type")
            print specinstypes
            returnDataList=[]
            for row in specinstypes:
                returnData = {}
                returnData['code'] = (row['instype']).split('/')[0]
                returnData['name'] = (row['instype']).split('/')[1]
                returnDataList.append(returnData)
            self.connection.close()
            return Response(json.dumps(returnDataList), mimetype='application/json')
        if oib and request.query_string != '':
            where = []
            for k,v in enumerate(request.args):
                print urllib.unquote(request.query_string).encode('utf8')
                subquery = ("%s LIKE '%s' AND " % (v, (request.args.get(v)).decode('utf-8')))
                where.append(subquery)
            print where
            exit()
        ##GET establishment id from oib
        self.connection.connect()
        estabid = self.connection.query("SELECT id from cide_establishment WHERE oib = '%s'" % oib)
        self.connection.close()
        ##GET coordinated inspections for estabid
        self.connection.connect()
        coordinspedata = self.connection.query("SELECT a.inspection_date DATE, concat(b.person_name,' ',b.person_surname) COORDINATOR from cide_coordinated_inspection a, cide_person b WHERE a.id_establishment = %s AND a.id_user = b.id_person" % estabid[0][0])
        if not coordinspedata:
            self.connection.close()
            return Response('{"message":"establishment %s has 0 coordinated inspections"}' % oib, mimetype='application/json')
        else:
            returnDataList = []
            returnDataList.append({"count": self.connection.numresult})
            for row in coordinspedata:
                returnData = {}
                returnData['inspection_date'] = (row['date']).strftime('%Y-%m-%d')
                returnData['inspection_coordinator'] = (row['coordinator'])
                returnDataList.append(returnData)
            self.connection.close()
            return Response(json.dumps(returnDataList), mimetype='application/json')

    @auth.login_required
    def post(self):
        loggeduser = g.user
        requestData = request.get_json()
        oib = requestData['oib']
        inspection_date = requestData['inspection_date']
        lastupdate = datetime.datetime.now().strftime('%Y-%m-%d')
        self.connection.connect()
        estabid = self.connection.query("SELECT id from cide_establishment WHERE oib = '%s'" % oib)
        idpersonrole = self.personclass.getPersonRoleId(loggeduser)
        print idpersonrole
        print("ID PERSON ROLE FOR COORDINATED INSPECTION INSERT IS:" + str(idpersonrole[2][0][0]))
        print("INSPECTION DATE FOR COORDINATED INSPECTION INSERT IS:" + inspection_date)
        print("ID ESTABLISHMENT FOR COORDINATED INSPECTION INSERT IS:" + str(estabid[0][0]))
        print("LAST UPDATE FOR COORDINATED INSPECTION INSERT IS:" + lastupdate)
        print("ID USER FOR COORDINATED INSPECTION INSERT IS:" + str(idpersonrole[0][0][0]))
        ## INSERT COORDINATED INSPECTION
        if 'ROLE_CIDE_ADMIN' in loggeduser[1] or 'ROLE_CIDE_COORDINATOR' in loggeduser[1]:
            if request.path.endswith('/insert'):
                insertcoordinatedinspection = self.connection.query("INSERT INTO cide_coordinated_inspection(id_person_role,id_establishment,inspection_date,id_user,last_update) VALUES (%s,%s,'%s','%s','%s') RETURNING id_coordinated_inspection" % (idpersonrole[2][0][0],estabid[0][0],inspection_date,idpersonrole[0][0][0],lastupdate),False)
                vec = 'insertedOK'
            elif request.path.endswith('/update'):
                coordinator = requestData['inspection_coordinator']
                idcoordinatedinspection=self.connection.query("SELECT a.id_coordinated_inspection FROM cide_coordinated_inspection a, cide_person b WHERE a.inspection_date = '%s' AND b.person_name = '%s' AND b.person_surname = '%s'" % (inspection_date,coordinator.split(' ')[0],coordinator.split(' ')[1]))
                print idcoordinatedinspection
                exit()
                insertspecificinspection = self.connection.query("UPDATE cide_coordinated_inspection SET inspection_date = %s" % (inspection_date), False)
                vec = 'updatedOK'
            self.connection.close()
            return Response('{"message":"OK"}',mimetype='application/json')
        else:
            print(loggeduser[1])
            return Response('{"message":"your role %s has no right to add/update coordinated inspection"}' % loggeduser[1][0], mimetype='application/json')