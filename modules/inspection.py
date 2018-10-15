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
        """
            CRITERIOR SCORE VALUES LIST /api/inspection/specific/criterior/score
            Available for any user role.
        """
        if request.path.endswith('/specific/criterior/score'):
            self.connection.connect()
            scoredatalist = self.connection.query("SELECT id_score ID, CONCAT(des_score,'-(',score_num::text,')') LIST from cide_score")
            self.connection.close()
            returnData=[]
            for value in scoredatalist:
                item = {}
                item['id'] = hashids.encode(value['id'])
                item['value'] = value['list']
                returnData.append(item)
            return Response(json.dumps(returnData, ensure_ascii=False), mimetype='application/json')

        """
            CRITERIOR VALUES FOR SPECIFIC INSPECTION TYPES /api/inspection/specific/criterior
            Data returned based on user role. CIDE_ROLE_ADMIN returns all.        
        """
        if request.path.endswith('/specific/criterior'):
            self.connection.connect()
            specInspTypes = []
            for type in self.connection.query("SELECT split_part(des_inspection_type, '/', 1) INSTYPE from cide_specific_inspection_type"):
                specInspTypes.append(type[0])
            #### FOR SAKE OF SIMPLICITY WE TAKE THE FIRST ROLE FROM ROLE LIST
            if any(ext in g.user[1][0] for ext in specInspTypes):
                idpersonrole = self.personclass.getPersonRoleId(g.user)
                self.connection.connect()
                inspectionTypeId = self.connection.query("SELECT id_inspection_type FROM cide_person_role WHERE id_person_role = %s" % idpersonrole[2][0][0])
                critfamid = self.connection.query("SELECT id_criterior_family ID, criterior_family FVALUE FROM cide_criterior_family") ### WHERE SPECIFIC INSPECTION TYPE ID
                returnDataList = []
                for family in critfamid:
                    families = {}
                    families['id'] = hashids.encode(family['id'])
                    families['value'] = family['fvalue']
                    criteriors = self.connection.query("SELECT a.id_criterior ID, a.des_criterior CVALUE FROM cide_criterior a, cide_specification_type_criterior x "
                                                       "WHERE x.id_inspection_type = %s AND "
                                                       "x.id_criterior = a.id_criterior AND "
                                                       "a.id_criterior_family = %s" % (inspectionTypeId[0][0],family['id']))
                    if criteriors:
                        criteriums = []
                        for kriterium in criteriors:
                            criterium = {}
                            criterium['id'] = hashids.encode(kriterium['id'])
                            criterium['value'] = kriterium['cvalue']
                            criteriums.append(criterium)
                        families['criteria'] = criteriums
                    returnDataList.append(families)
                self.connection.close()
                return Response(json.dumps(returnDataList, ensure_ascii=False), mimetype='application/json')
            elif 'ROLE_CIDE_ADMIN' in g.user[1] or 'ROLE_CIDE_COORDINATOR' in g.user[1]:
                self.connection.connect()
                critfamid = self.connection.query(
                    "SELECT id_criterior_family ID, criterior_family FVALUE FROM cide_criterior_family")  ### WHERE SPECIFIC INSPECTION TYPE ID
                returnDataList = []
                for family in critfamid:
                    families = {}
                    families['id'] = hashids.encode(family['id'])
                    families['value'] = family['fvalue']
                    criteriors = self.connection.query(
                        "SELECT id_criterior ID, des_criterior CVALUE FROM cide_criterior WHERE id_criterior_family = %s" %
                        family['id'])
                    if criteriors:
                        criteriums = []
                        for kriterium in criteriors:
                            criterium = {}
                            criterium['id'] = hashids.encode(kriterium['id'])
                            criterium['value'] = kriterium['cvalue']
                            criteriums.append(criterium)
                        families['criteria'] = criteriums
                    returnDataList.append(families)
                self.connection.close()
                return Response(json.dumps(returnDataList, ensure_ascii=False), mimetype='application/json')
        """
           INSERTION SPECIFIC INSPECTION TYPE ONLY FOR ADMIN /api/inspection/specific/type/insert?type=TEST&dismissed=True
        """
        '''
        if not hashid and not request.path.endswith('/specific/type') and not request.path.endswith('/specific/type/insert'):
            return Response('{"message":"missing filter"}', mimetype='application/json')
        '''
        if not hashid and request.path.endswith("/specific/type/insert"):
            if 'ROLE_CIDE_ADMIN' in g.user[1]:
                insptype = request.args.get('type')
                dismissed = request.args.get('dismissed')
                if insptype and dismissed:
                    self.connection.connect()
                    newtypeid = self.connection.query("INSERT INTO cide_specific_inspection_type(des_inspection_type,dismissed) VALUES ('%s',%s) RETURNING id_inspection_type" % (insptype,dismissed),False)
                    self.connection.close()
                    return Response('{"inserted":"%s"}' % hashids.encode(newtypeid[0][0]),mimetype='application/json')
                else:
                    return Response('{"message":"missing input data for inspection: type and dismissed"}', mimetype='application/json')

            else:
                return Response('{"message":"role %s is not allowed to use this endpoint"}' % g.user[1][0], mimetype='application/json')

        """
            SPECIFIC INSPECTIONS TYPES LIST /api/inspection/specific/type
        """
        if not hashid and request.path.endswith("/specific/type"):
            ## GET LIST OF SPEC INSP TYPES
            self.connection.connect()
            specinstypes = self.connection.query("SELECT des_inspection_type INSTYPE,id_inspection_type ID from cide_specific_inspection_type")
            print specinstypes
            returnDataList=[]
            for row in specinstypes:
                returnData = {}
                if 'ROLE_CIDE_ADMIN' in g.user[1]:
                    returnData['id'] = hashids.encode(row['id'])
                returnData['code'] = (row['instype']).split('/')[0]
                returnData['name'] = (row['instype']).split('/')[1]
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

                returnDataList.append(returnData)
            self.connection.close()
            return Response(json.dumps(returnDataList,ensure_ascii=False), mimetype='application/json')
        """
            GET DATA FOR SPECIFIC INSPECTION /api/inspection/specific/id_coordinated_inspection
            ROLES ADMIN + COORDINATOR RETRIEVES ALL FOR SELECTED COORDINATED INSPECTION
            ROLES 
        """
        if hashid and request.path.endswith('/specific/' + hashid):
            print('Endpoint to view specific inspection data')
            if 'ROLE_CIDE_SMS' in g.user[1] or 'ROLE_CIDE_IED' in g.user[1]:
                idpersonrole = self.personclass.getPersonRoleId(g.user)
                self.connection.connect()
                specinspecdata = self.connection.query("SELECT a.id_specific_inspection ID, "
                                                       "b.des_inspection_type SPECTYPE, "
                                                       "a.specific_inspection_date DATE, "
                                                       "concat(c.person_name,' ',c.person_surname) INSPECTOR, "
                                                       "a.final_report REPORT, "
                                                       "a.last_update UPDATED "
                                                       "FROM cide_specific_inspection a, cide_specific_inspection_type b, cide_person c, cide_person_role d "
                                                       "WHERE a.id_coordinated_inspection = %s "
                                                       "AND a.id_person_role = %s "
                                                       "AND d.id_person_role = a.id_person_role "
                                                       "AND c.id_person = d.id_person "
                                                       "AND b.id_inspection_type = d.id_inspection_type" % ((hashids.decode(hashid))[0],idpersonrole[2][0][0]))
                self.connection.close()
                if not specinspecdata:
                    return Response('{"message":"inspector %s has been asigned 0 specific inspections"}' % (hashids.encode(idpersonrole[0][0][0])),mimetype='application/json')
                else:
                    returnDataList = []
                    #returnDataList.append({"count": self.connection.numresult})
                    for row in specinspecdata:
                        returnData = {}
                        returnData['spec_inspection_type'] = (row['spectype'])
                        returnData['spec_inspection_date'] = (row['date']).strftime('%Y-%m-%d')
                        returnData['spec_inspection_inspector'] = (row['inspector'])
                        if row['report'] is None:
                            returnData['spec_inspection_report'] = (row['report'])
                        else:
                            returnData['spec_inspection_report'] = 1
                        returnData['spec_inspection_updated'] = (row['updated']).strftime('%Y-%m-%d')
                        returnData['id'] = (hashids.encode(row['id']))
                        returnDataList.append(returnData)
                    self.connection.close()
                    return Response(json.dumps(returnDataList, ensure_ascii=False), mimetype='application/json')
            elif 'ROLE_CIDE_ADMIN' in g.user[1] or 'ROLE_CIDE_COORDINATOR':
                self.connection.connect()
                print("ID COORD INSP: %s" % (hashids.decode(hashid))[0])
                specinspecdata = self.connection.query("SELECT a.id_specific_inspection ID, "
                                                       "b.des_inspection_type SPECTYPE, "
                                                       "a.specific_inspection_date DATE, "
                                                       "concat(c.person_name,' ',c.person_surname) INSPECTOR, "
                                                       "a.final_report REPORT, "
                                                       "a.last_update UPDATED "
                                                       "FROM cide_specific_inspection a, cide_specific_inspection_type b, cide_person c, cide_person_role d "
                                                       "WHERE a.id_coordinated_inspection = %s AND d.id_person_role = a.id_person_role AND c.id_person = d.id_person AND b.id_inspection_type = d.id_inspection_type" % (hashids.decode(hashid))[0])
                self.connection.close()
                if not specinspecdata:
                    return Response('{"message":"coordinated inspection %s has 0 specific inspections"}' % hashid,mimetype='application/json')
                else:
                    returnDataList = []
                    #returnDataList.append({"count": self.connection.numresult})
                    for row in specinspecdata:
                        returnData = {}
                        returnData['spec_inspection_type'] = (row['spectype'])
                        returnData['spec_inspection_date'] = (row['date']).strftime('%Y-%m-%d')
                        returnData['spec_inspection_inspector'] = (row['inspector'])
                        if row['report'] is None:
                            returnData['spec_inspection_report'] = (row['report'])
                        else:
                            returnData['spec_inspection_report'] = 1
                        returnData['id'] = (hashids.encode(row['id']))
                        returnData['spec_inspection_updated'] = (row['updated']).strftime('%Y-%m-%d')
                        returnDataList.append(returnData)
                    self.connection.close()
                    return Response(json.dumps(returnDataList, ensure_ascii=False), mimetype='application/json')
        """
            GET LIST OF ISSUES FOR SPECIFIC INSPECTION /api/inspection/specific/issue/id_coordinated_inspection
            ROLES ADMIN + COORDINATOR RETRIEVES ALL FOR SELECTED COORDINATED INSPECTION
            ROLES 
        """
        if hashid and request.path.endswith('/specific/issue/' + hashid):
            self.connection.connect()
            openissuesdata = self.connection.query("SELECT * FROM cide_open_issue WHERE id_specific_inspection = %s" % (hashids.decode(hashid))[0])
            print openissuesdata
            if not openissuesdata:
                self.connection.close()
                return Response('{"message":"specific inspection %s has 0 openned issues"}' % hashid,mimetype='application/json')
            else:
                returnDataList = []
                #returnDataList.append({"count": self.connection.numresult})
                for row in openissuesdata:
                    print row
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



        """
            GET LIST OF COORDINATED INSPECTION FOR ESTABLISHMENT ID/api/inspection/id_establishment
                    ROLES ADMIN + COORDINATOR RETRIEVES ALL FOR SELECTED COORDINATED INSPECTION
                    ROLES  
                """
        if hashid and request.path.endswith('/' + hashid):
            self.connection.connect()
            coordinspedata = self.connection.query("SELECT   a.id_coordinated_inspection ID, "
                                                            "a.inspection_date DATE, "
                                                            "concat(b.person_name,' ',b.person_surname) COORDINATOR, "
                                                            "count(c.id_specific_inspection) SICOUNT "
                                                    "FROM cide_coordinated_inspection a "
                                                    "LEFT JOIN cide_person b "
                                                    "ON a.id_user = b.id_person "
                                                    "LEFT JOIN cide_specific_inspection c "
                                                    "ON a.id_coordinated_inspection = c.id_coordinated_inspection "
                                                    "WHERE a.id_establishment = %s "
                                                    "GROUP BY a.id_coordinated_inspection, a.inspection_date, b.person_name, b.person_surname" %  (hashids.decode(hashid))[0])
            if not coordinspedata:
                self.connection.close()
                return Response('{"message":"establishment %s has 0 coordinated inspections"}' % hashid, mimetype='application/json')
            else:
                returnDataList = []
                #returnDataList.append({"count": self.connection.numresult})
                for row in coordinspedata:
                    returnData = {}
                    returnData['inspection_date'] = (row['date']).strftime('%Y-%m-%d')
                    returnData['inspection_coordinator'] = (row['coordinator'])
                    returnData['id'] = (hashids.encode(row['id']))
                    returnData['si_count'] = (row['sicount'])
                    returnDataList.append(returnData)
                self.connection.close()
                return Response(json.dumps(returnDataList,ensure_ascii=False), mimetype='application/json')

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
            if request.path.endswith('inspection/insert'):
                idestablishment = requestData['id']
                inspection_date = requestData['inspection_date']
                self.connection.connect()
                insertcoordinatedinspection = self.connection.query("INSERT INTO cide_coordinated_inspection(id_person_role,id_establishment,inspection_date,id_user,last_update) VALUES "
                                                                    "(%s,%s,'%s','%s','%s') RETURNING id_coordinated_inspection" %
                                                                    (idpersonrole[2][0][0],(hashids.decode(idestablishment))[0],inspection_date,idpersonrole[0][0][0],lastupdate),False)
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
                        print("Inserting score '%s' of criteria '%s' and comment '%s' for SI '%s'" % (hashids.decode(criteria['id_score'])[0], hashids.decode(criteria['id_criterior'])[0],criteria['comments'],hashids.decode(criteria['id_specific_inspection'])[0]))
                        insertCriteriumForSi = self.connection.query("INSERT INTO cide_specific_insp_criteria (id_specific_inspection, id_criterior, id_score, comments, id_user, last_update) VALUES "
                                                                                "(%s, %s, %s, '%s', %s, '%s') RETURNING id_specific_inspection" % (hashids.decode(criteria['id_specific_inspection'])[0], hashids.decode(criteria['id_criterior'])[0],
                                                                                                                 hashids.decode(criteria['id_score'])[0], criteria['comments'],idpersonrole[0][0][0],lastupdate), False)
                        if insertCriteriumForSi:
                            inserted = inserted + 1
                    else:
                        print("Updating score '%s' of criteria '%s' and comment '%s' for SI '%s'" % (hashids.decode(criteria['id_score'])[0], hashids.decode(criteria['id_criterior'])[0],criteria['comments'],id_specific_inspection[0][0]))
                        updateCriteriumForCi = self.connection.query("UPDATE cide_specific_insp_criteria SET"
                                                                     "  id_score=%s, comments='%s', id_user=%s, last_update = '%s' "
                                                                     "WHERE id_specific_inspection=%s AND id_criterior=%s RETURNING id_specific_inspection" % (hashids.decode(criteria['id_score'])[0],criteria['comments'],idpersonrole[0][0][0],
                                                                                                                              lastupdate,id_specific_inspection[0][0],hashids.decode(criteria['id_criterior'])[0]), False)
                        if updateCriteriumForCi:
                            updated = updated + 1
                    self.connection.close()
                    result = '{"inserted":'+str(inserted)+',"updated":'+str(updated)+'}'
                    print(result)
            #### INSERT ISSUES ####
            if request.path.endswith("/specific/issue/insert"):
                inserted = 0
                updated = 0
                for issue in requestData:
                    if 'issue_description' not in issue:
                        issue['issue_description'] = ''
                    if 'acc_warning' not in issue:
                        issue['acc_warning'] = ''
                    if 'des_indictment' not in issue:
                        issue['des_indictment'] = ''
                    if "id" in issue:
                        #UPDATING ISSUE
                        self.connection.connect()
                        updateIssue = self.connection.query("UPDATE cide_open_issue SET "
                                                            "id_specific_inspection=%s, des_open_issue='%s', acc_prescriptions=%s, deadline_warning='%s', acc_warning=%s, des_indictment='%s', id_user=%s, last_update='%s' "
                                                            "WHERE id_open_issue=%s RETURNING id_open_issue" % (hashids.decode(issue['id_specific_inspection'])[0],
                                                                            issue['issue_description'],
                                                                            issue['acc_prescriptions'],
                                                                            issue['deadline_warning'],
                                                                            issue['acc_warning'],
                                                                            issue['des_indictment'],
                                                                            idpersonrole[0][0][0],
                                                                            lastupdate,hashids.decode(issue['id'])[0]), False)
                        self.connection.close()
                        if updateIssue:
                            updated = updated + 1
                    else:
                        self.connection.connect()
                        insertIssue = self.connection.query("INSERT INTO cide_open_issue (id_specific_inspection, des_open_issue, acc_prescriptions, deadline_warning, acc_warning, des_indictment, id_user, last_update) VALUES "
                                                                                 "(%s,'%s',%s,'%s',%s,'%s',%s,'%s') RETURNING id_open_issue" % (hashids.decode(issue['id_specific_inspection'])[0],
                                                                                issue['issue_description'],
                                                                                issue['acc_prescriptions'],
                                                                                issue['deadline_warning'],
                                                                                issue['acc_warning'],
                                                                                issue['des_indictment'],
                                                                                idpersonrole[0][0][0],
                                                                                lastupdate), False)
                        self.connection.close()
                        if insertIssue:
                            inserted = inserted + 1
                    result = '{"inserted":' + str(inserted) + ',"updated":' + str(updated) + '}'
        if not result:
            return Response('{"message":"your role %s has no right to add/update coordinated/specific inspections"}' % g.user[1][0], mimetype='application/json',status=401)
        else:
            return Response(result, mimetype='application/json')