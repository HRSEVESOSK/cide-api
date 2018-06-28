# -*- coding: utf-8 -*-
import json,datetime,sys
from flask_restful import Resource
from hashids import Hashids
from flask import request, Response,g,jsonify
from flask_httpauth import HTTPBasicAuth
from modules import auth as authentication
from modules import person as Person
import lib.pgsql as pgsql
auth = HTTPBasicAuth()
hashids = Hashids(min_length=16)
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
    def get(self,hashid=False):
        if not hashid and not request.path.endswith("/types"):
            return Response('{"message":"missing oib filter"}', mimetype='application/json')
        if not hashid and request.path.endswith("/types"):
            ## GET LIST OF SPEC INSP TYPES
            self.connection.connect()
            specinstypes = self.connection.query("SELECT des_inspection_type INSTYPE,id_inspection_type ID from cide_specific_inspection_type")
            print specinstypes
            returnDataList=[]
            for row in specinstypes:
                returnData = {}
                returnData['code'] = (row['instype']).split('/')[0]
                ##APPEN INSPECTORS TO INSPECTION TYPES
                personids = self.connection.query("SELECT id_person IDP, id_person_role IDPR  FROM cide_person_role WHERE id_inspection_type = %s" % row['id'])
                print personids
                if personids:
                    inspectors = []
                    for person in personids:
                        inspector = {}
                        inspector['fullname'] = (self.connection.query("SELECT concat(person_name,' ',person_surname) FULLNAME FROM cide_person WHERE id_person = %s" % person[0]))[0][0]
                        inspector['id'] = hashids.encode(person[1])
                        inspectors.append(inspector)
                    returnData['inspectors'] = inspectors
                returnData['name'] = (row['instype']).split('/')[1]
                returnDataList.append(returnData)
            self.connection.close()
            return Response(json.dumps(returnDataList,ensure_ascii=False), mimetype='application/json')
        self.connection.connect()
        #estabid = self.connection.query("SELECT id from cide_establishment WHERE oib = '%s'" % oib)
        self.connection.close()
        ##GET coordinated inspections for estabid
        self.connection.connect()
        coordinspedata = self.connection.query("SELECT a.id_coordinated_inspection ID,a.inspection_date DATE, concat(b.person_name,' ',b.person_surname) COORDINATOR from cide_coordinated_inspection a, cide_person b WHERE a.id_establishment = %s AND a.id_user = b.id_person" %  (hashids.decode(hashid))[0])
        if not coordinspedata:
            self.connection.close()
            return Response('{"message":"establishment %s has 0 coordinated inspections"}' % hashid, mimetype='application/json')
        else:
            returnDataList = []
            returnDataList.append({"count": self.connection.numresult})
            for row in coordinspedata:
                returnData = {}
                returnData['inspection_date'] = (row['date']).strftime('%Y-%m-%d')
                returnData['inspection_coordinator'] = (row['coordinator'])
                returnData['id'] = (hashids.encode(row['id']))
                returnDataList.append(returnData)
            self.connection.close()
            return Response(json.dumps(returnDataList,ensure_ascii=False), mimetype='application/json')

    @auth.login_required
    def post(self):
        loggeduser = g.user
        requestData = request.get_json()
        idestablishment = requestData['id']
        inspection_date = requestData['inspection_date']
        lastupdate = datetime.datetime.now().strftime('%Y-%m-%d')
        self.connection.connect()
        #estabid = self.connection.query("SELECT id from cide_establishment WHERE oib = '%s'" % oib)
        idpersonrole = self.personclass.getPersonRoleId(loggeduser)
        ## INSERT COORDINATED INSPECTION
        if 'ROLE_CIDE_ADMIN' in loggeduser[1] or 'ROLE_CIDE_COORDINATOR' in loggeduser[1]:
            if request.path.endswith('/insert'):
                insertcoordinatedinspection = self.connection.query("INSERT INTO cide_coordinated_inspection(id_person_role,id_establishment,inspection_date,id_user,last_update) VALUES (%s,%s,'%s','%s','%s') RETURNING id_coordinated_inspection" % (idpersonrole[2][0][0],(hashids.decode(idestablishment))[0],inspection_date,idpersonrole[0][0][0],lastupdate),False)
                result = '{"inserted":"'+hashids.encode(insertcoordinatedinspection[0][0])+'"}'
            elif request.path.endswith('/update'):
                coordinator = requestData['inspection_coordinator']
                idpersonroleinspector = (hashids.decode(requestData['inspector_id_person_role']))[0]
                hashid = requestData['id']
                specinspdate = requestData['inspection_date']
                iduser = str(idpersonrole[0][0][0])
                insertspecificinspection = self.connection.query("INSERT INTO cide_specific_inspection(id_coordinated_inspection,id_person_role,specific_inspection_date,id_user,last_update) VALUES (%s,%s,'%s','%s','%s') RETURNING id_specific_inspection" % ((hashids.decode(hashid))[0],idpersonroleinspector,specinspdate,iduser,lastupdate), False)
                if insertspecificinspection:
                    #UPDATE METADATA FOR COORDINATED INSPECTION
                    updatecoordinspection = self.connection.query("UPDATE cide_coordinated_inspection SET last_update = '%s', id_user = '%s' WHERE id_coordinated_inspection = %s" % (lastupdate,iduser,(hashids.decode(hashid))[0]), False)
                    if updatecoordinspection:
                        result = '{"inserted":"'+hashids.encode(insertspecificinspection[0][0])+'"}'
            self.connection.close()
            return Response(result,mimetype='application/json')
        else:
            print(loggeduser[1])
            return Response('{"message":"your role %s has no right to add/update coordinated inspection"}' % loggeduser[1][0], mimetype='application/json')