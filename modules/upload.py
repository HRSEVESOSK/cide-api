import os,datetime,psycopg2,io
from flask import request,g,Response,send_file
from flask_restful import Resource
from werkzeug import secure_filename
from hashids import Hashids
hashids = Hashids(min_length=16)
from config import config as cfg
from modules import auth as authentication
from flask_httpauth import HTTPBasicAuth
from modules import person as Person
import lib.pgsql as pgsql
UPLOAD_FOLDER = cfg.tempDataDir
ALLOWED_EXTENSIONS = set(cfg.extensions)
auth = HTTPBasicAuth()
class Upload(Resource):
    def __init__(self):
        self.personclass = Person.Person()
        self.connection = pgsql.PGSql()
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
        personClass = Person.Person()
        person = personClass.checkLoggedUser(user)
        print("CHECK LOGGED USER STATUS: %s" % person)
        return True

    def allowed_file(self,filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


    def get(self,hashid=False):
        if request.path.endswith("/specific/download/" + hashid):
            inspectionType = 'specific'
            #hashid = 'QABWJxbojagwOL0E'
            self.connection.connect()
            selectReport = self.connection.query("SELECT final_report from cide_specific_inspection where id_specific_inspection=%s" % (hashids.decode(hashid))[0])
            self.connection.close()
        if request.path.endswith("/inspection/download/" + hashid):
            inspectionType = 'coordinated'
            self.connection.connect()
            selectReport = self.connection.query("SELECT final_report from cide_coordinated_inspection where id_coordinated_inspection=%s" % (hashids.decode(hashid))[0])
            self.connection.close()
        if selectReport[0][0]:
            return send_file(io.BytesIO(selectReport[0][0]), mimetype='application/pdf', as_attachment=True,attachment_filename='Report_'+inspectionType+'_'+ hashid + '.pdf')
            #return send_file(io.BytesIO(selectReport[0][0]))
        else:
            return Response('{"message":"specificic inspection %s has not report in CIDE datatabase"}' % hashid, mimetype='application/json',status=404)


    @auth.login_required
    def post(self):
        idpersonrole = self.personclass.getPersonRoleId(g.user)
        file = request.files['file']
        hashid = request.form['id']
        print(g.user)
        if request.path.endswith('/inspection/specific/upload'):
            inspectionType = 'specific'
        if request.path.endswith('/inspection/upload'):
            inspectionType = 'coordinated'

        if not self.allowed_file(file.filename):
            return Response('"message":"file extension forbidden"', mimetype='application/json',status=403)

        if file and self.allowed_file(file.filename):
            filename = secure_filename(file.filename)
            ciReportFolder = os.path.join(UPLOAD_FOLDER, inspectionType, hashid)
            if not os.path.exists(ciReportFolder):
                os.makedirs(ciReportFolder)
            reportPath = os.path.join(ciReportFolder, filename)
            file.save(reportPath)
            ## HERE WE NEED TO UPDATE DATABASE
            if os.path.isfile(reportPath) and os.path.getsize(reportPath) > 0:
                print("Report file {0} sucesfully uploaded. Updating database for CI ID: {1}".format(os.path.join(ciReportFolder, filename), hashid))
                iduser = str(idpersonrole[0][0][0])
                lastupdate = datetime.datetime.now().strftime('%Y-%m-%d')
                # UPDATE METADATA FOR COORDINATED INSPECTION ADDING SPECIFIC INSPECTIONS
                reportBlob = open(reportPath, 'rb')
                self.connection.connect()
                updatecoordinspection = self.connection.query(
                    "UPDATE cide_%s_inspection SET "
                    "last_update = '%s', "
                    "id_user = %s, "
                    "final_report = %s"
                    " WHERE "
                    "id_%s_inspection = %s "
                    "RETURNING id_%s_inspection" % (
                        inspectionType,
                        lastupdate,
                        iduser,
                        psycopg2.Binary(reportBlob.read()),
                        inspectionType,
                        (hashids.decode(hashid))[0],
                        inspectionType
                    ), False)
                self.connection.close()
                reportBlob.close()
                print updatecoordinspection
                if updatecoordinspection:
                    result = '{"updated":"' + hashids.encode(updatecoordinspection[0][0]) + '"}'
                    return Response(result, mimetype='application/json')
        else:
            result = '{"updated": 0}'


        return Response(result, mimetype='application/json')

        #if 'ROLE_CIDE_ADMIN' in g.user[1] or 'ROLE_CIDE_COORDINATOR' or 'ROLE_CIDE_SMS' in g.user[1]:

