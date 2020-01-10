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
        self.connection = pgsql.PGSql()


    @auth.verify_password
    def verify_pw(username, password):
        authenticate = authentication.Authentication()
        user = authenticate.verify_user_pass(username, password)
        if not user:
            return False
        g.user = user
        check = personcheck.Person()
        person = check.checkLoggedUser(user)
        print("CHECK LOGGED USER STATUS: %s" % person)
        return True


    @auth.login_required
    def get(self):
        if request.args:
            for argument in request.args:
                if argument == 'name':
                    SQL = "SELECT oib OIB, establishment_name MUN_NAME, naziv MUNIC, concat(street,' ',street_number) ADDR, cide_establishment.id ESTABID, count(id_coordinated_inspection) CICOUNT, company_name FIRMA " \
                          "FROM cide_establishment " \
                          "LEFT JOIN cide_coordinated_inspection ON cide_coordinated_inspection.id_establishment = cide_establishment.id " \
                          "LEFT JOIN rpot_postanskiured ON rpot_postanskiured.id = cide_establishment.city_id " \
                          "WHERE establishment_name LIKE %s " \
                          "GROUP BY OIB,MUN_NAME,MUNIC,ADDR,ESTABID " \
                          "ORDER BY max(last_update) DESC NULLS LAST"

                    self.connection.connect()
                    establishment_data = self.connection.query(sql=SQL,data=[(request.args.get(argument)).encode("utf-8")])
                    self.connection.close()
                elif argument == 'oib':
                    SQL="SELECT oib OIB, establishment_name MUN_NAME, naziv MUNIC, concat(street,' ',street_number) ADDR, cide_establishment.id ESTABID, count(id_coordinated_inspection) CICOUNT, company_name FIRMA " \
                        "FROM cide_establishment " \
                        "LEFT JOIN cide_coordinated_inspection ON cide_coordinated_inspection.id_establishment = cide_establishment.id " \
                        "LEFT JOIN rpot_postanskiured ON rpot_postanskiured.id = cide_establishment.city_id " \
                        "WHERE oib LIKE %s " \
                        "GROUP BY OIB,MUN_NAME,MUNIC,ADDR,ESTABID ORDER BY max(last_update) DESC NULLS LAST "
                    self.connection.connect()
                    establishment_data = self.connection.query(sql=SQL,data=[((request.args.get(argument)).encode("utf-8")).replace('*', '%')])
                    self.connection.close()
                else:
                    return Response('{"message":"parameter %s not available"}' % str(argument),mimetype='application/json',status=400)
        else:
            #sqlSelect = ("select oib OIB,establishment_name MUN_NAME,city_id MUNIC,concat(street,' ',street_number) ADDR, id ESTABID from cide_establishment GROUP BY OIB,MUN_NAME,MUNIC,ADDR,ESTABID")
            if 'ROLE_CIDE_ADMIN' in g.user[1] or 'ROLE_CIDE_COORDINATOR' in g.user[1]:
                SQL="SELECT oib OIB,establishment_name MUN_NAME,naziv MUNIC,concat(street,' ',street_number) ADDR,cide_establishment.id ESTABID,count(id_coordinated_inspection) CICOUNT, company_name FIRMA " \
                    "FROM cide_establishment " \
                    "LEFT JOIN cide_coordinated_inspection ON cide_coordinated_inspection.id_establishment = cide_establishment.id " \
                    "LEFT JOIN rpot_postanskiured ON rpot_postanskiured.id = cide_establishment.city_id " \
                    "GROUP BY OIB,MUN_NAME,MUNIC,ADDR,ESTABID " \
                    "ORDER BY max(last_update) DESC NULLS LAST"
                self.connection.connect()
                establishment_data = self.connection.query(sql=SQL)
                self.connection.close()
            else:
                id_person_role = self.personclass.getPersonRoleId(g.user)
                SQL="SELECT id_inspection_type FROM cide_person_role WHERE id_person_role = %s"
                self.connection.connect()
                id_inspection_type = self.connection.query(sql=SQL,data=[id_person_role[2][0][0]])
                self.connection.close()
                SQL = "SELECT oib OIB,establishment_name MUN_NAME,naziv MUNIC,concat(street,' ',street_number) ADDR,cide_establishment.id ESTABID,count(cide_coordinated_inspection.id_coordinated_inspection) CICOUNT, company_name FIRMA " \
                      "FROM cide_establishment " \
                      "LEFT JOIN cide_coordinated_inspection ON cide_coordinated_inspection.id_establishment = cide_establishment.id " \
                      "LEFT JOIN rpot_postanskiured ON rpot_postanskiured.id = cide_establishment.city_id " \
                      "LEFT JOIN cide_specific_inspection ON cide_coordinated_inspection.id_coordinated_inspection = cide_specific_inspection.id_coordinated_inspection " \
                      "WHERE cide_specific_inspection.id_person_role in (select id_person_role from cide_person_role where id_inspection_type = %s ) " \
                      "GROUP BY OIB,MUN_NAME,MUNIC,ADDR,ESTABID " \
                      "ORDER BY max(cide_coordinated_inspection.last_update) DESC NULLS LAST"
                self.connection.connect()
                establishment_data = self.connection.query(sql=SQL,data=[id_inspection_type[0][0]])
                self.connection.close()
        if not establishment_data:
            return Response(status=404)
        else:
            return_data= []
            for row in establishment_data:
                item = {}
                item['oib'] = (row['oib'])
                item['establishment_name'] = (row['mun_name'])
                item['establishment_municipality'] = (row['munic'])
                item['establishment_address'] = (row['addr'])
                item['id'] = (hashids.encode(row['estabid']))
                item['ci_count'] = row['cicount']
                item['establishment_operator'] = row['firma']
                return_data.append(item)
            return Response(json.dumps(return_data,ensure_ascii=False), mimetype='application/json')
