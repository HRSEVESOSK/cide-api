import os
from flask import request,g,Response
from flask_restful import Resource
from werkzeug import secure_filename
from config import config as cfg
from modules import auth as authentication
from flask_httpauth import HTTPBasicAuth
from modules import person as Person
UPLOAD_FOLDER = cfg.tempDataDir
ALLOWED_EXTENSIONS = set(cfg.extensions)
auth = HTTPBasicAuth()
class Upload(Resource):
    def __init__(self):
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
        personClass = Person.Person()
        person = personClass.checkLoggedUser(user)
        print("CHECK LOGGED USER STATUS: %s" % person)
        return True

    def allowed_file(self,filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

    def post(self):
        #idpersonrole = self.personclass.getPersonRoleId(g.user)
        file = request.files['file']
        if request.path.endswith('/inspection/specific/upload'):
            if file and self.allowed_file(file.filename):
                filename = secure_filename(file.filename)
                ciReportFolder = os.path.join(UPLOAD_FOLDER,filename.split('.')[0])
                if not os.path.exists(ciReportFolder):
                    os.makedirs(ciReportFolder)
                file.save(os.path.join(ciReportFolder, filename))
                result = '{"uploaded":"' + file.filename + '","path":"' + os.path.join(UPLOAD_FOLDER,file.filename) + '"}'
            else:
                result = '{"uploaded": 0}'
        return Response(result, mimetype='application/json')

        #if 'ROLE_CIDE_ADMIN' in g.user[1] or 'ROLE_CIDE_COORDINATOR' or 'ROLE_CIDE_SMS' in g.user[1]:

