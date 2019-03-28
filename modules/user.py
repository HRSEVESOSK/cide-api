# -*- coding: utf-8 -*-
import lib.pgsql as pgsql
from hashids import Hashids
from flask_httpauth import HTTPBasicAuth
from flask_restful import Resource
from flask import g,Response,request,jsonify
from modules import person as personcheck
from modules import auth as authentication
import json
auth = HTTPBasicAuth()
hashids = Hashids(min_length=16)
import sys
reload(sys)
sys.setdefaultencoding('utf8')
class User(Resource):
    def __init__(self):
        self.connection = pgsql.PGSql()
        self.personclass = personcheck.Person()

    @auth.verify_password
    def verify_pw(username, password):
        authenticate = authentication.Authentication()
        user = authenticate.verify_user_pass(username, password)
        print(user)
        if not user:
            return False
        g.user = user
        # g.user = user[0]
        # CHECK IF USER AND ROLES EXIST IN cide_person and cide_role tables, if not create one if yes return OK
        check = personcheck.Person()
        person = check.checkLoggedUser(user)
        print("CHECK LOGGED USER STATUS: %s" % person)
        return True
    @auth.login_required
    def get(self):
        if 'ROLE_CIDE_ADMIN' in g.user[1]:
            self.connection.connect()
            sqlSelect = 'SELECT cide_person.id_person,' \
                        'cide_person.person_name,' \
                        'cide_person.person_surname,' \
                        'cide_person.gs_username,' \
                        'cide_person.email,' \
                        'cide_role.gs_role ' \
                        'from cide_person ' \
                        'JOIN cide_person_role ON cide_person.id_person = cide_person_role.id_person ' \
                        'JOIN cide_role ON cide_person_role.id_role = cide_role.id_role'
            data = self.connection.query(sqlSelect)
            self.connection.close()
            if data:
                returnDataList = []
                # returnDataList.append({"count": connection.numresult})
                for row in data:
                    returnData = {}
                    returnData['id'] = (hashids.encode(row['id_person']))
                    returnData['person_name'] = (row['person_name'])
                    returnData['person_surnname'] = (row['person_surname'])
                    returnData['person_email'] = (row['email'])
                    returnData['person_username'] = (row['gs_username'])
                    returnData['person_role'] = (row['gs_role'])
                    returnDataList.append(returnData)
                return Response(json.dumps(returnDataList, ensure_ascii=False), mimetype='application/json')
        else:
            return Response('Unauthorized',401)
    @auth.login_required
    def post(self):
        if 'ROLE_CIDE_ADMIN' in g.user[1]:
            postData = request.json
            uId=(hashids.decode(postData['id']))[0]
            uName=postData['person_name'].encode('utf-8')
            uSurname=postData['person_surnname'].encode('utf-8')
            uEmail=postData['person_email'].encode('utf-8')
            print("USER OID: {}".format(uId))
            print("USER NAME: {}".format(uName))
            print("USER SURNNAME: {}".format(uSurname))
            print("USER EMAIL: {}".format(uEmail))
            self.connection.connect()
            updateCidePerson = self.connection.query("UPDATE cide_person SET person_name='%s', person_surname='%s', email='%s' WHERE id_person=%s RETURNING id_person" % (uName,uSurname,uEmail,uId),False)
            self.connection.close()
            if updateCidePerson:
                result = '{"updated":"' + hashids.encode(updateCidePerson[0][0]) + '"}'
            else:
                result = '{"updated":"0"}'
            return Response(result)

