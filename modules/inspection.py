# -*- coding: utf-8 -*-
import json,datetime,sys,requests
from flask_restful import Resource
from hashids import Hashids
from flask import request, Response,g,jsonify
from flask_httpauth import HTTPBasicAuth
from modules import auth as authentication
from modules import person as Person
from config import config as cfg
import lib.pgsql as pgsql
auth = HTTPBasicAuth()
hashids = Hashids(min_length=16)

class Inspection(Resource):
    def __init__(self):
        self.connection =  pgsql.PGSql()
        self.personclass = Person.Person()
        self.apiBaseUrl = 'http://' + cfg.host + ':' + cfg.apiport + '/api'
    @auth.verify_password
    def verify_pw(username, password):
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
    def post(self):
        specInspTypes = []
        result = False
        self.connection.connect()
        for type in self.connection.query("SELECT split_part(des_inspection_type, '/', 1) from cide_specific_inspection_type"):
            specInspTypes.append(type[0])
        self.connection.close()
        idpersonrole = self.personclass.getPersonRoleId(g.user)
        requestData = request.get_json()
        lastupdate = datetime.datetime.now().strftime('%Y-%m-%d')
        ## INSERT COORDINATED INSPECTION
        if 'ROLE_CIDE_ADMIN' in g.user[1] or 'ROLE_CIDE_COORDINATOR' in g.user[1]: # or 'ROLE_CIDE_SMS' in g.user[1]:
            if request.path.endswith('/inspection/insert'):
                idestablishment = requestData['id']
                inspection_date = requestData['inspection_date']
                inspection_type = requestData['inspection_type']
                self.connection.connect()
                insertcoordinatedinspection = self.connection.query("INSERT INTO cide_coordinated_inspection(id_person_role,id_establishment,inspection_date,id_user,last_update,type) VALUES "
                                                                    "(%s,%s,'%s','%s','%s','%s') RETURNING id_coordinated_inspection" %
                                                                    (idpersonrole[2][0][0],(hashids.decode(idestablishment))[0],inspection_date,idpersonrole[0][0][0],lastupdate,inspection_type),False)
                self.connection.close()
                result = '{"inserted":"'+hashids.encode(insertcoordinatedinspection[0][0])+'"}'
            elif request.path.endswith('/specific/delete'):
                hashid = requestData['id']
                self.connection.connect()
                deletespecificinspection = self.connection.query("DELETE FROM cide_specific_inspection WHERE id_specific_inspection = %s RETURNING id_specific_inspection" % (hashids.decode(hashid)[0]), False)
                self.connection.close()

                if deletespecificinspection:
                    result = '{"deleted":"' + hashids.encode(deletespecificinspection[0][0]) + '"}'
                else:
                    result = '{"deleted":0}'
            elif request.path.endswith('/delete'):
                hashid = requestData['id']
                self.connection.connect()
                deletespecificinspection = self.connection.query("DELETE FROM cide_coordinated_inspection WHERE id_coordinated_inspection = %s RETURNING id_coordinated_inspection" % (hashids.decode(hashid)[0]),False)
                self.connection.close()
                if deletespecificinspection:
                    result = '{"deleted":"'+hashids.encode(deletespecificinspection[0][0])+'"}'
                else:
                    result = '{"deleted":0}'
            elif request.path.endswith('/update'):
                coordinator = requestData['inspection_coordinator']
                idpersonroleinspector = (hashids.decode(requestData['inspector_id_person_role']))[0]
                hashid = requestData['id']
                specinspdate = requestData['inspection_date']
                iduser = str(idpersonrole[0][0][0])
                print("**** INSERTING RECORD to SI table")
                self.connection.connect()
                insertspecificinspection = self.connection.query("INSERT INTO cide_specific_inspection(id_coordinated_inspection,id_person_role,specific_inspection_date,id_user,last_update) VALUES "
                                                                 "(%s,%s,'%s','%s','%s') RETURNING id_specific_inspection" % ((hashids.decode(hashid))[0],idpersonroleinspector,specinspdate,iduser,lastupdate), False)
                self.connection.close()
                print("**** UPDATING record for coordinated inspecton to SI table")
                if insertspecificinspection:
                    #UPDATE METADATA FOR COORDINATED INSPECTION ADDING SPECIFIC INSPECTIONS
                    self.connection.connect()
                    updatecoordinspection = self.connection.query("UPDATE cide_coordinated_inspection SET last_update = '%s', id_user = '%s' WHERE id_coordinated_inspection = %s" % (lastupdate,iduser,(hashids.decode(hashid))[0]), False)
                    self.connection.close()
                    if updatecoordinspection:
                        result = '{"inserted":"'+hashids.encode(insertspecificinspection[0][0])+'"}'
        elif any(ext in g.user[1][0] for ext in specInspTypes):
            #### INSERT OR UDPATE CITERIA SCORING #####
            if request.path.endswith("/specific/criterior/insert"):
                inserted = 0
                updated = 0
                for criteria in requestData:
                    if 'comments' not in criteria:
                        criteria['comments'] = ''
                    self.connection.connect()
                    #CHECK IF DB
                    id_specific_inspection = self.connection.query("SELECT id_specific_inspection FROM "
                                                                   "cide_specific_insp_criteria WHERE "
                                                                   "id_specific_inspection=%s AND "
                                                                   "id_criterior=%s"
                                                                   % (hashids.decode(criteria['id_specific_inspection'])[0], hashids.decode(criteria['id_criterior'])[0]))
                    if not id_specific_inspection:
                        #INSERTING
                        print("Inserting score '%s' of criteria '%s' and comment '%s' for SI '%s'" % (hashids.decode(criteria['id_score'])[0], hashids.decode(criteria['id_criterior'])[0],(criteria['comments']).encode("utf-8"),hashids.decode(criteria['id_specific_inspection'])[0]))
                        insertCriteriumForSi = self.connection.query("INSERT INTO cide_specific_insp_criteria (id_specific_inspection, id_criterior, id_score, comments, id_user, last_update) VALUES "
                                                                                "(%s, %s, %s, '%s', %s, '%s') RETURNING id_specific_inspection" % (hashids.decode(criteria['id_specific_inspection'])[0], hashids.decode(criteria['id_criterior'])[0],
                                                                                                                 hashids.decode(criteria['id_score'])[0], (criteria['comments']).encode("utf-8"),idpersonrole[0][0][0],lastupdate), False)

                        if insertCriteriumForSi:
                            inserted = inserted + 1
                    else:
                        print("Updating score '%s' of criteria '%s' and comment '%s' for SI '%s'" % (hashids.decode(criteria['id_score'])[0], hashids.decode(criteria['id_criterior'])[0],(criteria['comments']).encode("utf-8"),id_specific_inspection[0][0]))
                        updateCriteriumForCi = self.connection.query("UPDATE cide_specific_insp_criteria SET"
                                                                     "  id_score=%s, comments='%s', id_user=%s, last_update = '%s' "
                                                                     "WHERE id_specific_inspection=%s AND id_criterior=%s RETURNING id_specific_inspection" % (hashids.decode(criteria['id_score'])[0],(criteria['comments']).encode("utf-8"),idpersonrole[0][0][0],
                                                                                                                              lastupdate,id_specific_inspection[0][0],hashids.decode(criteria['id_criterior'])[0]), False)
                        if updateCriteriumForCi:
                            updated = updated + 1
                    self.connection.close()
                if inserted > 0 or updated > 0:
                    self.connection.connect()
                    updateSIUpdateDate=self.connection.query("UPDATE cide_specific_inspection SET last_update='%s' WHERE id_specific_inspection=%s RETURNING id_specific_inspection" % (lastupdate,hashids.decode(criteria['id_specific_inspection'])[0]), False)
                    if updateSIUpdateDate:
                        print("SPecific inspection id '%s' sucessfully updated." % updateSIUpdateDate[0][0])
                result = '{"inserted":'+str(inserted)+',"updated":'+str(updated)+'}'
            #### INSERT ISSUES ####
            if request.path.endswith("/specific/issue/insert"):
                inserted = 0
                updated = 0
                deleted = 0
                currentIssues = []
                for issue in requestData:
                    if 'issue_description' not in issue:
                        issue['issue_description'] = ''
                    if 'acc_warning' not in issue:
                        issue['acc_warning'] = ''
                    if 'des_indictment' not in issue:
                        issue['des_indictment'] = ''
                    if 'acc_prescriptions' not in issue:
                        issue['acc_prescriptions'] = ''
                    if "id" in issue:
                        currentIssues.append(hashids.decode(issue['id'])[0])
                        #UPDATING ISSUE
                        self.connection.connect()
                        updateIssue = self.connection.query("UPDATE cide_open_issue SET "
                                                            "id_specific_inspection=%s, des_open_issue='%s', acc_prescriptions=%s, deadline_warning='%s', acc_warning=%s, des_indictment='%s', id_user=%s, last_update='%s' "
                                                            "WHERE id_open_issue=%s RETURNING id_open_issue" % (hashids.decode(issue['id_specific_inspection'])[0],
                                                                                                                (issue['issue_description']).encode("utf-8"),
                                                                                                                issue['acc_prescriptions'],
                                                                                                                issue['deadline_warning'],
                                                                                                                issue['acc_warning'],
                                                                                                                (issue['des_indictment']).encode("utf-8"),
                                                                                                                idpersonrole[0][0][0],
                                                                                                                lastupdate,
                                                                                                                hashids.decode(issue['id'])[0]), False)
                        self.connection.close()
                        if updateIssue:
                            updated = updated + 1
                    else:
                        self.connection.connect()
                        insertIssue = self.connection.query("INSERT INTO cide_open_issue (id_specific_inspection, des_open_issue, acc_prescriptions, deadline_warning, acc_warning, des_indictment, id_user, last_update) VALUES "
                                                                                 "(%s,'%s',%s,'%s',%s,'%s',%s,'%s') RETURNING id_open_issue" %
                                                            (hashids.decode(issue['id_specific_inspection'])[0],
                                                            (issue['issue_description']).encode("utf-8"),
                                                            issue['acc_prescriptions'],
                                                            issue['deadline_warning'],
                                                            issue['acc_warning'],
                                                            (issue['des_indictment']).encode("utf-8"),
                                                            idpersonrole[0][0][0],
                                                            lastupdate.encode("utf-8")),
                                                            False)
                        self.connection.close()
                        if insertIssue:
                            currentIssues.append(insertIssue[0][0])
                            inserted = inserted + 1
                ## CHECK DELETED
                self.connection.connect()
                ### CHECK DELETED ISSUES
                issuesForCI = self.connection.query("SELECT id_open_issue FROM cide_open_issue WHERE "
                                                    "id_specific_inspection=%s" % (hashids.decode(issue['id_specific_inspection'])[0]))
                issuesForCIFlattened = [item for sublist in issuesForCI for item in sublist]
                if len(issuesForCIFlattened) != len(currentIssues):
                    toBedeleted = set(issuesForCIFlattened).difference(currentIssues)
                    toBedeletedOids = list(toBedeleted)
                    if len(toBedeletedOids) > 0:
                        self.connection.connect()
                        deleteIssues = self.connection.query("DELETE FROM cide_open_issue WHERE id_open_issue IN (%s) RETURNING id_open_issue" % (','.join(map(str,toBedeletedOids))),False)
                        print("DELETED ISSUES: ", deleteIssues)
                        if deleteIssues:
                            deleted = deleted + len(deleteIssues)
                result = '{"inserted":' + str(inserted) + ',"updated":' + str(updated) + ',"deleted":'+str(deleted)+'}'
        if not result:
            return Response('{"message":"your role %s has no right to add/update coordinated/specific inspections"}' % g.user[1][0], mimetype='application/json',status=401)
        else:
            return Response(result, mimetype='application/json')
''' 
REFACTORED CODE START
'''
class Coordinated(Inspection):
    @auth.login_required
    def get(self, hashid):
        if hashid:
            if 'ROLE_CIDE_ADMIN' in g.user[1] or 'ROLE_CIDE_COORDINATOR' in g.user[1]:
                SQL = "SELECT " \
                      "a.id_coordinated_inspection ID, " \
                      "a.inspection_date DATE, " \
                      "concat(b.person_name,' ',b.person_surname) COORDINATOR, " \
                      "b.gs_username USERNAME, " \
                      "count(c.id_specific_inspection) SICOUNT, " \
                      "a.type as CITYPE, " \
                      "a.final_report as REPORT " \
                      "FROM cide_coordinated_inspection a " \
                      "LEFT JOIN cide_person b " \
                      "ON a.id_user = b.id_person " \
                      "LEFT JOIN cide_specific_inspection c " \
                      "ON a.id_coordinated_inspection = c.id_coordinated_inspection " \
                      "WHERE a.id_establishment = %s " \
                      "GROUP BY a.id_coordinated_inspection, a.inspection_date, b.person_name, b.person_surname, b.gs_username " \
                      "ORDER BY max(c.last_update) DESC NULLS LAST"
                self.connection.connect()
                coordinated_inspection_data = self.connection.query(sql=SQL, data=[(hashids.decode(hashid))[0]])
                self.connection.close()
            else:
                id_person_role = self.personclass.getPersonRoleId(g.user)
                SQL = "SELECT id_inspection_type FROM cide_person_role WHERE id_person_role = %s"
                self.connection.connect()
                id_inspection_type_data = self.connection.query(sql=SQL,data=[id_person_role[2][0][0]])
                self.connection.close()
                SQL="SELECT a.id_coordinated_inspection ID, " \
                    "a.inspection_date DATE, " \
                    "concat(b.person_name,' ',b.person_surname) COORDINATOR, " \
                    "b.gs_username USERNAME, " \
                    "count(c.id_specific_inspection) SICOUNT, " \
                    "a.type as CITYPE, " \
                    "a.final_report as REPORT " \
                    "FROM cide_coordinated_inspection a " \
                    "LEFT JOIN cide_person b " \
                    "ON a.id_user = b.id_person " \
                    "LEFT JOIN cide_specific_inspection c " \
                    "ON a.id_coordinated_inspection = c.id_coordinated_inspection " \
                    "WHERE a.id_establishment = %s " \
                    "AND c.id_person_role in (SELECT id_person_role FROM cide_person_role where id_inspection_type = %s) " \
                    "GROUP BY a.id_coordinated_inspection, a.inspection_date, b.person_name, b.person_surname, b.gs_username " \
                    "ORDER BY max(c.last_update) DESC NULLS LAST"
                self.connection.connect()
                coordinated_inspection_data = self.connection.query(sql=SQL,data=((hashids.decode(hashid))[0], id_inspection_type_data[0][0]))
                self.connection.close()
            if not coordinated_inspection_data:
                return Response('{"message":"establishment %s has 0 coordinated inspections"}' % hashid,mimetype='application/json')
            else:
                return_data = []
                for row in coordinated_inspection_data:
                    item = {}
                    item['inspection_date'] = (row['date']).strftime('%Y-%m-%d')
                    item['inspection_coordinator'] = (row['coordinator'])
                    item['inspection_coordinator_username'] = (row['username'])
                    item['inspection_type'] = (row['citype'])
                    if row['report'] is None:
                        item['inspection_report'] = (row['report'])
                    else:
                        item['inspection_report'] = 1
                    item['id'] = (hashids.encode(row['id']))
                    item['si_count'] = (row['sicount'])
                    return_data.append(item)
                return Response(json.dumps(return_data, ensure_ascii=False), mimetype='application/json')


    @auth.login_required
    def post(self):
        specific_inspection_types = []
        SQL = "SELECT split_part(des_inspection_type, '/', 1) from cide_specific_inspection_type"
        self.connection.connect()
        for type in self.connection.query(sql=SQL):
            specific_inspection_types.append(type[0])
        self.connection.close()
        id_person_role = self.personclass.getPersonRoleId(g.user)
        payload_data = request.get_json()
        last_updated = datetime.datetime.now().strftime('%Y-%m-%d')
        ## INSERT COORDINATED INSPECTION
        if 'ROLE_CIDE_ADMIN' in g.user[1] or 'ROLE_CIDE_COORDINATOR' in g.user[1]:
            oid_establishment = payload_data['id']
            inspection_date = payload_data['inspection_date']
            inspection_type = payload_data['inspection_type']
            SQL="INSERT INTO cide_coordinated_inspection(id_person_role,id_establishment,inspection_date,id_user,last_update,type) VALUES (%s,%s,%s,%s,%s,%s) RETURNING id_coordinated_inspection"
            self.connection.connect()
            insert_data=self.connection.query(sql=SQL,data=(id_person_role[2][0][0], (hashids.decode(oid_establishment))[0], inspection_date, id_person_role[0][0][0],last_updated, inspection_type),fetch=False)
            self.connection.close()
            if insert_data:
                return_data = '{"inserted":"' + hashids.encode(insert_data[0][0]) + '"}'
            else:
                return_data = '{"inserted":0}'
            return Response(return_data,mimetype='application/json')
        else:
            Response(status=403)


    @auth.login_required
    def delete(self,hashid):
        if 'ROLE_CIDE_ADMIN' in g.user[1] or 'ROLE_CIDE_COORDINATOR' in g.user[1]:
            coordinated_inspection_oid = (hashids.decode(hashid))[0]
            SQL = "DELETE FROM cide_coordinated_inspection WHERE id_coordinated_inspection = %s RETURNING id_coordinated_inspection"
            self.connection.connect()
            delete_coordinated_inspection = self.connection.query(sql=SQL, data=[coordinated_inspection_oid],fetch=False)
            self.connection.close()
            if delete_coordinated_inspection:
                return_data = '{"deleted":"' + hashids.encode(delete_coordinated_inspection[0][0]) + '"}'
            else:
                return_data = '{"deleted":0}'
            return Response(return_data, mimetype='application/json')
        else:
            return Response(status=403)


    @auth.login_required
    def put(self):
        if 'ROLE_CIDE_ADMIN' in g.user[1] or 'ROLE_CIDE_COORDINATOR' in g.user[1]:
            id_person_role = self.personclass.getPersonRoleId(g.user)
            payload_data = request.get_json()
            last_updated = datetime.datetime.now().strftime('%Y-%m-%d')
            id_person_role_inspector = (hashids.decode(payload_data['inspector_id_person_role']))[0]
            hashid = payload_data['id']
            specific_inspection_date = payload_data['inspection_date']
            id_user = str(id_person_role[0][0][0])
            SQL="INSERT INTO cide_specific_inspection(id_coordinated_inspection,id_person_role,specific_inspection_date,id_user,last_update) VALUES (%s,%s,%s,%s,%s) RETURNING id_specific_inspection"
            self.connection.connect()
            insert_specific_inspection_data = self.connection.query(sql=SQL,data=((hashids.decode(hashid))[0], id_person_role_inspector, specific_inspection_date, id_user, last_updated), fetch=False)
            self.connection.close()
            if insert_specific_inspection_data:
                SQL="UPDATE cide_coordinated_inspection SET last_update = %s, id_user = %s WHERE id_coordinated_inspection = %s RETURNING id_coordinated_inspection"
                self.connection.connect()
                update_coordinated_inspection = self.connection.query(sql=SQL,data=(last_updated, id_user, (hashids.decode(hashid))[0]), fetch=False)
                self.connection.close()
                if update_coordinated_inspection:
                    return_data = '{"updated":"' + hashids.encode(update_coordinated_inspection[0][0]) + '"}'
                else:
                    return_data = '{"updated":0}'
            else:
                return_data = '{"inserted":0}'
            return Response(return_data,mimetype='application/json')
        else:
            return Response(status=403)


class Specific(Inspection):
    def _generate_specific_inspection_resp_data(self,specific_inspection_data):
        returnDataList = []
        # returnDataList.append({"count": self.connection.numresult})
        for row in specific_inspection_data:
            returnData = {}
            returnData['spec_inspection_type'] = (row['spectype'])
            returnData['spec_inspection_date'] = (row['date']).strftime('%Y-%m-%d')
            returnData['spec_inspection_inspector'] = (row['inspector'])
            returnData['spec_inspection_organisation'] = (row['organisation'])
            if row['report'] is None:
                returnData['spec_inspection_report'] = (row['report'])
            else:
                returnData['spec_inspection_report'] = 1
            if row['sms_form'] is None:
                returnData['spec_inspection_sms_form'] = (row['sms_form'])
            else:
                returnData['spec_inspection_sms_form'] = 1
            if row['minutes'] is None:
                returnData['spec_inspection_minutes'] = (row['minutes'])
            else:
                returnData['spec_inspection_minutes'] = 1
            returnData['id'] = (hashids.encode(row['id']))
            returnData['spec_inspection_updated'] = (row['updated']).strftime('%Y-%m-%d')
            #returnData['issues_count'] = (row['countissue'])
            #returnData['crit_count'] = (row['countcrit'])
            returnDataList.append(returnData)
        return returnDataList


    @auth.login_required
    def get(self,hashid):
        language = request.args.get('lang')
        coordinated_inspection_oid = (hashids.decode(hashid))[0]
        if 'ROLE_CIDE_ADMIN' in g.user[1] or 'ROLE_CIDE_COORDINATOR' in g.user[1]:
            if not language or language == 'en':
                SQL = "SELECT a.id_specific_inspection ID, " \
                      "b.des_inspection_type SPECTYPE, " \
                      "a.specific_inspection_date DATE, " \
                      "concat(c.person_name,' ',c.person_surname) INSPECTOR, " \
                      "c.organisation ORGANISATION, " \
                      "a.final_report REPORT, " \
                      "a.sms_form SMS_FORM, " \
                      "a.minutes MINUTES, " \
                      "a.last_update UPDATED, " \
                      "count(e.id_specific_inspection) COUNTCRIT, " \
                      "count(f.id_specific_inspection) COUNTISSUE " \
                      "FROM cide_specific_inspection a " \
                      "LEFT JOIN cide_person_role d on d.id_person_role = a.id_person_role " \
                      "LEFT JOIN cide_person c on c.id_person = d.id_person " \
                      "LEFT JOIN cide_specific_inspection_type b on b.id_inspection_type = d.id_inspection_type " \
                      "LEFT JOIN cide_specific_insp_criteria e on e.id_specific_inspection = a.id_specific_inspection " \
                      "LEFT JOIN cide_open_issue f on f.id_specific_inspection = a.id_specific_inspection " \
                      "WHERE a.id_coordinated_inspection = %s " \
                      "AND d.id_person_role = a.id_person_role " \
                      "AND c.id_person = d.id_person " \
                      "AND b.id_inspection_type = d.id_inspection_type " \
                      "GROUP BY ID, SPECTYPE, DATE, INSPECTOR, ORGANISATION, REPORT " \
                      "ORDER BY  max(a.last_update) DESC NULLS LAST"
            else:
                SQL = "SELECT a.id_specific_inspection ID, " \
                      "b.des_inspection_type_hrv SPECTYPE, " \
                      "a.specific_inspection_date DATE, " \
                      "concat(c.person_name,' ',c.person_surname) INSPECTOR, " \
                      "c.organisation ORGANISATION, " \
                      "a.final_report REPORT, " \
                      "a.sms_form SMS_FORM, " \
                      "a.minutes MINUTES, " \
                      "a.last_update UPDATED, " \
                      "count(e.id_specific_inspection) COUNTCRIT, " \
                      "count(f.id_specific_inspection) COUNTISSUE " \
                      "FROM cide_specific_inspection a " \
                      "LEFT JOIN cide_person_role d on d.id_person_role = a.id_person_role " \
                      "LEFT JOIN cide_person c on c.id_person = d.id_person " \
                      "LEFT JOIN cide_specific_inspection_type b on b.id_inspection_type = d.id_inspection_type " \
                      "LEFT JOIN cide_specific_insp_criteria e on e.id_specific_inspection = a.id_specific_inspection " \
                      "LEFT JOIN cide_open_issue f on f.id_specific_inspection = a.id_specific_inspection " \
                      "WHERE a.id_coordinated_inspection = %s " \
                      "AND d.id_person_role = a.id_person_role " \
                      "AND c.id_person = d.id_person " \
                      "AND b.id_inspection_type = d.id_inspection_type " \
                      "GROUP BY ID, SPECTYPE, DATE, INSPECTOR, ORGANISATION, REPORT " \
                      "ORDER BY  max(a.last_update) DESC NULLS LAST"
            self.connection.connect()
            specific_inspection_data = self.connection.query(sql=SQL, data=[coordinated_inspection_oid])
            self.connection.close()
            if not specific_inspection_data:
                return Response('{"message":"coordinated inspection %s has 0 specific inspections"}' % hashid,mimetype='application/json')
            else:
                return_data = self._generate_specific_inspection_resp_data(specific_inspection_data)
        #if set(g.user[1]).issubset(cfg.siroles):
        else:
            id_person_role = self.personclass.getPersonRoleId(g.user)
            SQL = "SELECT id_inspection_type FROM cide_person_role WHERE id_person_role = %s"
            self.connection.connect()
            id_inspection_type = self.connection.query(sql=SQL,data=[id_person_role[2][0][0]])
            self.connection.close()
            if not language or language == 'en':
                SQL = "SELECT a.id_specific_inspection ID, " \
                      "b.des_inspection_type SPECTYPE, " \
                      "a.specific_inspection_date DATE, " \
                      "concat(c.person_name,' ',c.person_surname) INSPECTOR, " \
                      "c.organisation ORGANISATION, " \
                      "a.final_report REPORT, " \
                      "a.sms_form SMS_FORM, " \
                      "a.minutes MINUTES, " \
                      "a.last_update UPDATED " \
                      "FROM cide_specific_inspection a, cide_specific_inspection_type b, cide_person c, cide_person_role d " \
                      "WHERE a.id_coordinated_inspection = %s " \
                      "AND a.id_person_role in (select id_person_role from cide_person_role where id_inspection_type = %s ) " \
                      "AND d.id_person_role = a.id_person_role " \
                      "AND c.id_person = d.id_person " \
                      "AND b.id_inspection_type = d.id_inspection_type " \
                      "GROUP BY ID, SPECTYPE, DATE, INSPECTOR, ORGANISATION, REPORT " \
                      "ORDER BY max(a.last_update) DESC NULLS LAST"
            else:
                SQL = "SELECT a.id_specific_inspection ID, " \
                      "b.des_inspection_type_hrv SPECTYPE, " \
                      "a.specific_inspection_date DATE, " \
                      "concat(c.person_name,' ',c.person_surname) INSPECTOR, " \
                      "c.organisation ORGANISATION, " \
                      "a.final_report REPORT, " \
                      "a.sms_form SMS_FORM, " \
                      "a.minutes MINUTES, " \
                      "a.last_update UPDATED " \
                      "FROM cide_specific_inspection a, cide_specific_inspection_type b, cide_person c, cide_person_role d " \
                      "WHERE a.id_coordinated_inspection = %s " \
                      "AND a.id_person_role in (select id_person_role from cide_person_role where id_inspection_type = %s ) " \
                      "AND d.id_person_role = a.id_person_role " \
                      "AND c.id_person = d.id_person " \
                      "AND b.id_inspection_type = d.id_inspection_type " \
                      "GROUP BY ID, SPECTYPE, DATE, INSPECTOR, ORGANISATION, REPORT " \
                      "ORDER BY  max(a.last_update) DESC NULLS LAST"
            self.connection.connect()
            specific_inspection_data = self.connection.query(sql=SQL,data=(coordinated_inspection_oid,id_inspection_type[0][0]))
            self.connection.close()
            if not specific_inspection_data:
                return Response('{"message":"inspector %s has been asigned 0 specific inspections"}' % (hashids.encode(id_person_role[0][0][0])), mimetype='application/json')
            else:
                return_data = self._generate_specific_inspection_resp_data(specific_inspection_data)
        return Response(json.dumps(return_data, ensure_ascii=False), mimetype='application/json')


    @auth.login_required
    def delete(self,hashid):
        specific_inspection_oid = (hashids.decode(hashid))[0]
        SQL = "DELETE FROM cide_specific_inspection WHERE id_specific_inspection = %s RETURNING id_specific_inspection"
        self.connection.connect()
        delete_specific_inspection = self.connection.query(sql=SQL,data=[specific_inspection_oid])
        self.connection.close()
        if delete_specific_inspection:
            return_data = '{"deleted":"' + hashids.encode(delete_specific_inspection[0][0]) + '"}'
        else:
            return_data = '{"deleted":0}'
        return Response(return_data, mimetype='application/json')


class SpecificTypes(Inspection):
    @auth.login_required
    def get(self):
        id_person_role = self.personclass.getPersonRoleId(g.user)
        ## GET LIST OF SPEC INSP TYPES
        inspection_type = request.args.get('type')
        if inspection_type not in ['CI','SI']:
            return Response(status=400)
        language = request.args.get('lang')
        if not language or language == 'en':
            SQL = "SELECT des_inspection_type INSTYPE,id_inspection_type ID FROM cide_specific_inspection_type "
        else:
            SQL = "SELECT des_inspection_type_hrv INSTYPE,id_inspection_type ID FROM cide_specific_inspection_type "
        if inspection_type:
            SQL = SQL + "WHERE type='{}'".format(inspection_type)
        else:
            SQL = SQL + "WHERE 1=1"
        self.connection.connect()
        specific_inspection_types_data= self.connection.query(sql=SQL)
        self.connection.close()
        returnDataList = []
        for row in specific_inspection_types_data:
            returnData = {}
            if 'ROLE_CIDE_ADMIN' in g.user[1]:
                returnData['id'] = hashids.encode(row['id'])
            returnData['code'] = (row['instype']).split('/')[0]
            returnData['name'] = (row['instype']).split('/')[1]
            ##APPEN INSPECTORS TO INSPECTION TYPES
            SQL = "SELECT id_person FROM cide_person_role WHERE id_inspection_type = %s"
            self.connection.connect()
            inspectors = self.connection.query(sql=SQL,data=[row['id']])
            self.connection.close()
            inspectors_ids = tuple(int(l[0]) for l in inspectors)
            if inspectors:
                SQL = "SELECT concat(a.person_name,' ',a.person_surname) FULLNAME, " \
                      "a.gs_username USERNAME, " \
                      "a.organisation ORGANISATION, " \
                      "a.id_person IDP, " \
                      "b.id_person_role IDR " \
                      "FROM cide_person a " \
                      "LEFT JOIN cide_person_role b ON a.id_person=b.id_person " \
                      "WHERE a.id_person in %s"
                self.connection.connect()
                inspectors_data = self.connection.query(sql=SQL, data=[inspectors_ids])
                self.connection.close()
                inspectors = []
                for person in inspectors_data:
                    inspector = {}
                    inspector['fullname'] = person[0]
                    inspector['username'] = person[1]
                    inspector['organisation'] = person[2]
                    inspector['id'] = hashids.encode(person[4])
                    #inspector['idr'] = hashids.encode(person[4])
                    inspectors.append(inspector)
                returnData['inspectors'] = inspectors
            returnDataList.append(returnData)
        return Response(json.dumps(returnDataList, ensure_ascii=False), mimetype='application/json')


class Issue(Inspection):
    @auth.login_required
    def get(self,hashid):
        id_person_role = self.personclass.getPersonRoleId(g.user)
        oid_specific_inspection = (hashids.decode(hashid))[0]
        SQL = "SELECT * FROM cide_open_issue WHERE id_specific_inspection = %s"
        self.connection.connect()
        issue_data = self.connection.query(sql=SQL,data=[oid_specific_inspection])
        self.connection.close()
        if not issue_data:
            return Response('{"message":"specific inspection %s has 0 openned issues"}' % hashid,mimetype='application/json')
        returnDataList = []
        for row in issue_data:
            returnData = {}
            returnData['id'] = (hashids.encode(row[0]))
            returnData['issue_description'] = row[2]
            returnData['acc_prescriptions'] = row[3]
            returnData['deadline_warning'] = (row[4]).strftime('%Y-%m-%d')
            returnData['acc_warning'] = row[5]
            returnData['des_indictment'] = row[6]
            returnData['last_update'] = (row[8]).strftime('%Y-%m-%d')
            returnData['id_specific_inspection'] = hashid
            returnDataList.append(returnData)
            self.connection.close()
        return Response(json.dumps(returnDataList, ensure_ascii=False), mimetype='application/json')


class Score(Inspection):
    @auth.login_required
    def get(self,hashid):
        id_person_role = self.personclass.getPersonRoleId(g.user)
        oid_specific_inspection = (hashids.decode(hashid))[0]
        SQL = "SELECT * FROM cide_specific_insp_criteria WHERE id_specific_inspection = %s"
        self.connection.connect()
        score_data = self.connection.query(sql=SQL,data=[oid_specific_inspection])
        self.connection.close()
        if not score_data:
            return Response('{"message":"specific inspection %s has 0 scores created"}' % hashid,mimetype='application/json')
        scores = []
        for row in score_data:
            returnData = {}
            returnData['id_specific_inspection'] = hashids.encode(row[0])
            returnData['id_criterior'] = hashids.encode(row[1])
            returnData['id_score'] = hashids.encode(row[2])
            returnData['comments'] = row[3]
            returnData['id_user'] = hashids.encode(row[4])
            returnData['last_update'] = (row[5]).strftime('%Y-%m-%d')
            scores.append(returnData)
        return Response(json.dumps(scores, ensure_ascii=False), mimetype='application/json')


    @auth.login_required
    def post(self):
        id_person_role = self.personclass.getPersonRoleId(g.user)
        payload_data = request.get_json()
        last_updated = datetime.datetime.now().strftime('%Y-%m-%d')
        inserted = 0
        updated = 0
        for criteria in payload_data:
            if 'comments' not in criteria:
                criteria['comments'] = ''
            SQL="SELECT id_specific_inspection FROM cide_specific_insp_criteria WHERE id_specific_inspection=%s AND id_criterior=%s"
            self.connection.connect()
            id_specific_inspection = self.connection.query(sql=SQL,data=(hashids.decode(criteria['id_specific_inspection'])[0],hashids.decode(criteria['id_criterior'])[0]))
            self.connection.close()
            if not id_specific_inspection:
                SQL="INSERT INTO cide_specific_insp_criteria (id_specific_inspection, id_criterior, id_score, comments, id_user, last_update) " \
                    "VALUES (%s, %s, %s, %s, %s, %s) " \
                    "RETURNING id_specific_inspection"
                self.connection.connect()
                insert_criterium_si_data = self.connection.query(sql=SQL,data=(hashids.decode(criteria['id_specific_inspection'])[0],
                                                                               hashids.decode(criteria['id_criterior'])[0],
                                                                               hashids.decode(criteria['id_score'])[0], (criteria['comments']).encode("utf-8"),
                                                                               id_person_role[0][0][0], last_updated), fetch=False)
                self.connection.close()
                if insert_criterium_si_data:
                    inserted += 1
            else:
                SQL="UPDATE cide_specific_insp_criteria " \
                    "SET id_score=%s, comments=%s, id_user=%s, last_update = %s " \
                    "WHERE id_specific_inspection=%s AND id_criterior=%s " \
                    "RETURNING id_specific_inspection"
                self.connection.connect()
                update_criterium_si_data = self.connection.query(sql=SQL,data=(hashids.decode(criteria['id_score'])[0],
                                                                               (criteria['comments']).encode("utf-8"),
                                                                               id_person_role[0][0][0],last_updated,
                                                                               id_specific_inspection[0][0],
                                                                               hashids.decode(criteria['id_criterior'])[0]),fetch=False)
                self.connection.close()
                if update_criterium_si_data:
                    updated = updated + 1

        if inserted > 0 or updated > 0:
            SQL="UPDATE cide_specific_inspection SET last_update='%s' WHERE id_specific_inspection=%s RETURNING id_specific_inspection"
            self.connection.connect()
            self.connection.query(sql=SQL,data=(last_updated, hashids.decode(criteria['id_specific_inspection'])[0]), fetch=False)
            self.connection.close()
        return_data = '{"inserted":' + str(inserted) + ',"updated":' + str(updated) + '}'
        return Response(return_data,mimetype='application/json')


class CriteriaScore(Inspection):
    @auth.login_required
    def get(self):
        language = request.args.get('lang')
        if not language or language == 'en':
            SQL = ("SELECT id_score ID, CONCAT(des_score,'-(',score_num::text,')') LIST from cide_score")
        else:
            SQL = ("SELECT id_score ID, CONCAT(des_score_hrv,'-(',score_num::text,')') LIST from cide_score")
        self.connection.connect()
        score_data = self.connection.query(sql=SQL)
        self.connection.close()
        returnData = []
        for value in score_data:
            item = {}
            item['id'] = hashids.encode(value['id'])
            item['value'] = value['list']
            returnData.append(item)
        return Response(json.dumps(returnData, ensure_ascii=False), mimetype='application/json')


class Criteria(Inspection):
    @auth.login_required
    def get(self):
        language = request.args.get('lang')
        if not language or language == 'en':
            SQL1 = "SELECT id_criterior_family ID, criterior_family FVALUE FROM cide_criterior_family"
            SQL2 = "SELECT id_criterior ID, des_criterior CVALUE FROM cide_criterior WHERE id_criterior_family = %s"
        else:
            SQL1 = ("SELECT id_criterior_family ID, criterior_family FVALUE FROM cide_criterior_family")
            SQL2 = "SELECT id_criterior ID, des_criterior_hrv CVALUE FROM cide_criterior WHERE id_criterior_family = %s"
        self.connection.connect()
        criteria_family_data = self.connection.query(sql=SQL1)
        self.connection.close()
        returnDataList = []
        for family in criteria_family_data:
            families = {}
            families['id'] = hashids.encode(family['id'])
            families['value'] = family['fvalue']
            self.connection.connect()
            criteriors_data = self.connection.query(sql=SQL2,data=[family['id']])
            self.connection.close()
            if criteriors_data:
                criteriums = []
                for kriterium in criteriors_data:
                    criterium = {}
                    criterium['id'] = hashids.encode(kriterium['id'])
                    criterium['value'] = kriterium['cvalue']
                    criteriums.append(criterium)
                families['criteria'] = criteriums
            returnDataList.append(families)
        return Response(json.dumps(returnDataList, ensure_ascii=False), mimetype='application/json')
