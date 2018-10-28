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
    @auth.verify_password
    def verify_pw(username, password):
        authenticate = authentication.Authentication()
        user = authenticate.verify_user_pass(username, password)
        print(user)
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
        connection = pgsql.PGSql()
        if request.args:
            for argument in request.args:
                ### ADDED GROUP BY TO AVOID DUPLICATES ###
                if argument == 'name':
                    sqlSelect = ("SELECT oib OIB, establishment_name MUN_NAME, naziv MUNIC, concat(street,' ',street_number) ADDR, cide_establishment.id ESTABID, count(id_coordinated_inspection) CICOUNT, company_name FIRMA "
                                 "FROM cide_establishment "
                                 "LEFT JOIN cide_coordinated_inspection ON cide_coordinated_inspection.id_establishment = cide_establishment.id "
                                 "LEFT JOIN rpot_postanskiured ON rpot_postanskiured.id = cide_establishment.city_id "
                                 "WHERE establishment_name LIKE '%s' GROUP BY OIB,MUN_NAME,MUNIC,ADDR,ESTABID,last_update ORDER BY last_update DESC NULLS LAST" % ((request.args.get(argument)).encode("utf-8")).replace('*', '%'))
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
                                 "WHERE oib LIKE '%s' GROUP BY OIB,MUN_NAME,MUNIC,ADDR,ESTABID,last_update ORDER BY last_update DESC NULLS LAST" % ((request.args.get(argument)).encode("utf-8")).replace('*', '%'))
                    connection.connect()
                    data = connection.query(sql=sqlSelect)
                    connection.close()
                    continue
                else:
                    return Response('{"message":"parameter %s not available"}' % str(argument),mimetype='application/json')
        else:
            #sqlSelect = ("select oib OIB,establishment_name MUN_NAME,city_id MUNIC,concat(street,' ',street_number) ADDR, id ESTABID from cide_establishment GROUP BY OIB,MUN_NAME,MUNIC,ADDR,ESTABID")
            sqlSelect = ("select oib OIB,establishment_name MUN_NAME,naziv MUNIC,concat(street,' ',street_number) ADDR,cide_establishment.id ESTABID,count(id_coordinated_inspection) CICOUNT, company_name FIRMA "
                         "FROM cide_establishment "
                         "LEFT JOIN cide_coordinated_inspection ON cide_coordinated_inspection.id_establishment = cide_establishment.id "
                         "LEFT JOIN rpot_postanskiured ON rpot_postanskiured.id = cide_establishment.city_id "
                         "GROUP BY OIB,MUN_NAME,MUNIC,ADDR,ESTABID,last_update "
                         "ORDER BY last_update DESC NULLS LAST")
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

        '''    
            sendQuery = SQL.selectQuery(table='cide_establishment',where=)
            print(argument)
            query.append({argument:request.args.get(argument)})
            subquery = ("%s LIKE '%s' AND " % (argument,request.args.get(argument)))
            where.append(subquery)
        input_dict = json.load(open('data/establishments.json'))
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
        #return Response(open('data/establishments.json'), mimetype='application/json')
        '''