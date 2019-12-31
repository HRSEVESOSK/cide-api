#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from hashids import Hashids
from flask_restful import Resource
from flask import request, Response,g,jsonify
from flask_httpauth import HTTPBasicAuth
from modules import auth as authentication
import lib.pgsql as pgsql
from modules import person as personcheck
auth = HTTPBasicAuth()
hashids = Hashids(min_length=16)
class Establishment(Resource):
    def __init__(self):
        self.personclass = personcheck.Person()
    @auth.verify_password
    def verify_pw(username, password):
        authenticate = authentication.Authentication()
        user = authenticate.verify_user_pass(username, password)
        print(user)
        if not user:
            return False
        g.user = user
        #g.user = user[0]
        # CHECK IF USER AND ROLES EXIST IN cide_person and cide_role tables, if not create one if yes return OK
        check = personcheck.Person()
        person = check.checkLoggedUser(user)
        print("CHECK LOGGED USER STATUS: %s" % person)
        return True
    @auth.login_required
    def get(self):
        connection = pgsql.PGSql()
        if request.args:
            for argument in request.args:
                ### ADDED GROUP BY TO AVOID DUPLICATES ###
                if argument == 'name':
                    sqlSelect = ("SELECT oib OIB, establishment_name MUN_NAME, naziv MUNIC, concat(street,' ',street_number) ADDR, cide_establishment.id ESTABID, count(id_coordinated_inspection) CICOUNT, company_name FIRMA "
                                 "FROM cide_establishment "
                                 "LEFT JOIN cide_coordinated_inspection ON cide_coordinated_inspection.id_establishment = cide_establishment.id "
                                 "LEFT JOIN rpot_postanskiured ON rpot_postanskiured.id = cide_establishment.city_id "
                                 "WHERE establishment_name LIKE '%s' GROUP BY OIB,MUN_NAME,MUNIC,ADDR,ESTABID ORDER BY max(last_update) DESC NULLS LAST" % ((request.args.get(argument)).encode("utf-8")).replace('*', '%'))
                    connection.connect()
                    data = connection.query(sqlSelect)
                    #data = connection.query(sql=sqlSelect)
                    connection.close()
                    continue
                elif argument == 'oib':
                    sqlSelect = ("SELECT oib OIB, establishment_name MUN_NAME, naziv MUNIC, concat(street,' ',street_number) ADDR, cide_establishment.id ESTABID, count(id_coordinated_inspection) CICOUNT, company_name FIRMA "
                                 "FROM cide_establishment "
                                 "LEFT JOIN cide_coordinated_inspection ON cide_coordinated_inspection.id_establishment = cide_establishment.id "
                                 "LEFT JOIN rpot_postanskiured ON rpot_postanskiured.id = cide_establishment.city_id "
                                 "WHERE oib LIKE '%s' GROUP BY OIB,MUN_NAME,MUNIC,ADDR,ESTABID ORDER BY max(last_update) DESC NULLS LAST" % ((request.args.get(argument)).encode("utf-8")).replace('*', '%'))
                    connection.connect()
                    data = connection.query(sql=sqlSelect)
                    connection.close()
                    continue
                else:
                    return Response('{"message":"parameter %s not available"}' % str(argument),mimetype='application/json')
        else:
            #sqlSelect = ("select oib OIB,establishment_name MUN_NAME,city_id MUNIC,concat(street,' ',street_number) ADDR, id ESTABID from cide_establishment GROUP BY OIB,MUN_NAME,MUNIC,ADDR,ESTABID")
            if 'ROLE_CIDE_ADMIN' in g.user[1] or 'ROLE_CIDE_COORDINATOR' in g.user[1]:
                sqlSelect = ("select oib OIB,establishment_name MUN_NAME,naziv MUNIC,concat(street,' ',street_number) ADDR,cide_establishment.id ESTABID,count(id_coordinated_inspection) CICOUNT, company_name FIRMA "
                             "FROM cide_establishment "
                             "LEFT JOIN cide_coordinated_inspection ON cide_coordinated_inspection.id_establishment = cide_establishment.id "
                             "LEFT JOIN rpot_postanskiured ON rpot_postanskiured.id = cide_establishment.city_id "
                             "GROUP BY OIB,MUN_NAME,MUNIC,ADDR,ESTABID "
                             "ORDER BY max(last_update) DESC NULLS LAST")
            else:
                idpersonrole = self.personclass.getPersonRoleId(g.user)
                id_inspection_type_select = "select id_inspection_type from cide_person_role where id_person_role = %s" % idpersonrole[2][0][0]
                connection.connect()
                id_inspection_type = connection.query(id_inspection_type_select)
                connection.close()
                sqlSelect = ("select oib OIB,establishment_name MUN_NAME,naziv MUNIC,concat(street,' ',street_number) ADDR,cide_establishment.id ESTABID,count(cide_coordinated_inspection.id_coordinated_inspection) CICOUNT, company_name FIRMA "
                             "FROM cide_establishment "
                             "LEFT JOIN cide_coordinated_inspection ON cide_coordinated_inspection.id_establishment = cide_establishment.id "
                             "LEFT JOIN rpot_postanskiured ON rpot_postanskiured.id = cide_establishment.city_id "
                             "LEFT JOIN cide_specific_inspection ON cide_coordinated_inspection.id_coordinated_inspection = cide_specific_inspection.id_coordinated_inspection "
                             "WHERE cide_specific_inspection.id_person_role in (select id_person_role from cide_person_role where id_inspection_type = %s ) "
                             "GROUP BY OIB,MUN_NAME,MUNIC,ADDR,ESTABID "
                             "ORDER BY max(cide_coordinated_inspection.last_update) DESC NULLS LAST" % id_inspection_type[0][0])
            print sqlSelect
            connection.connect()
            data = connection.query(sqlSelect)
            connection.close()
        if data:
            returnDataList = []
            #returnDataList.append({"count": connection.numresult})
            for row in data:
                returnData = {}
                returnData['oib'] = (row['oib'])
                returnData['establishment_name'] = (row['mun_name'])
                returnData['establishment_municipality'] = (row['munic'])
                returnData['establishment_address'] = (row['addr'])
                returnData['id'] = (hashids.encode(row['estabid']))
                returnData['ci_count'] = row['cicount']
                returnData['establishment_operator'] = row['firma']
                returnDataList.append(returnData)
            return Response(json.dumps(returnDataList,ensure_ascii=False), mimetype='application/json')
