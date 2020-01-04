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
import logging
UPLOAD_FOLDER = cfg.tempDataDir
ALLOWED_EXTENSIONS = set(cfg.extensions)
auth = HTTPBasicAuth()
class UploadDocument(Resource):
    def __init__(self):
        self.personclass = Person.Person()
        self.connection = pgsql.PGSql()
    

    @auth.verify_password
    def verify_pw(username, password):
        print(username)
        print(password)
        authenticate = authentication.Authentication()
        user = authenticate.verify_user_pass(username, password)
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


    def update_inspection_table_with_document(self, document, blob, inspection_type, oid):
    	id_person_role = self.person_class.getPersonRoleId(g.user)
    	id_user = str(id_person_role[0][0][0])
    	updated_date = datetime.datetime.now().strftime('%Y-%m-%d')
    	if inspection_type == 'specific':
    		table_name = 'cide_specific_inspection'
    		id_collumn = 'id_specific_inspection'
    	else:
    		table_name = 'cide_coordinated_inspection'
    		id_collumn = 'id_coordinated_inspection'
    	SQL = "UPDATE %s SET last_update = %s, id_user %s, %s = %s WHERE %s = %s RETURNING %s"
    	self.connection.connect()
    	update_data = self.connection.query(sql=SQL, data=(table_name,updated_date,id_user,document, psycopg2.Binary(blob.read()), id_collumn, oid, id_collumn), fetch=False)
    	self.connection.close()
    	return update_data


    @auth.login_required
    def post(self):
        file = request.files['file']
        hashid = request.form['id']
        doc_type = request.form['document']
        inspection_type = request.form['type']
        if not file or not hashid or not doc_type or not inspection_type:
        	return Response(status=400)
        oid = (hashids.decode(hashid))[0]
        if not self.allowed_file(file.filename):
            return Response('{"message":"file extension forbidden"}', mimetype='application/json',status=400)
        filename = secure_filename(file.filename)
        document_folder = os.path.join(UPLOAD_FOLDER, inspection_type, hashid)
        if not os.path.exists(document_folder):
            os.makedirs(document_folder)
        filepath = os.path.join(document_folder, filename)
        file.save(filepath)
        lastupdate = datetime.datetime.now().strftime('%Y-%m-%d')
        if os.path.isfile(filepath):
        	with open(filepath, 'rb') as document_blob:
        		update_database=self.update_inspection_table_with_document(doc_type,document_blob,inspection_type,oid)
    		if update_database:
    			result = '{"updated":"' + hashids.encode(updatecoordinspection[0][0]) + '"}'
    		else:
    			result = '{"updated": 0}'
        else:
        	result = '{"updated": 0}'
        return Response(result, mimetype='application/json')


class DownloadDocument(Resource):
    def __init__(self):
        self.personclass = Person.Person()
        self.connection = pgsql.PGSql()


    @auth.verify_password
    def verify_pw(username, password):
        authenticate = authentication.Authentication()
        user = authenticate.verify_user_pass(username, password)
        if not user:
            return False
        g.user = user
        # CHECK IF USER AND ROLES EXIST IN cide_person and cide_role tables, if not create one if yes return OK
        personClass = Person.Person()
        person = personClass.checkLoggedUser(user)
        print("CHECK LOGGED USER STATUS: %s" % person)
        return True


    def select_inspection_document(self, document, inspection_type, oid):
    	updated_date = datetime.datetime.now().strftime('%Y-%m-%d')
    	if inspection_type == 'specific':
    		table_name = 'cide_specific_inspection'
    		id_collumn = 'id_specific_inspection'
    	else:
    		table_name = 'cide_coordinated_inspection'
    		id_collumn = 'id_coordinated_inspection'
    	SQL = "SELECT %s FROM %s WHERE %s=%s"
    	self.connection.connect()
    	update_data = self.connection.query(sql=SQL, data=(document,table_name,id_collumn,oid))
    	self.connection.close()
    	return update_data


    def get(self):
    	doc_type = request.args.get('document')
    	inspection_type = request.args.get('type')
    	inspection_hash = request.args.get('hash')
    	if not doc_type or not inspection_type or not inspection_hash:
    		return Response(status=400)
    	inspection_oid = (hashids.decode(inspection_hash))[0]
    	select_document = self.select_inspection_document()
        if select_document:
            attachment_filename = "{0}_{1}_{2}.pdf".format(doc_type,inspection_type,inspection_hash)
            return send_file(io.BytesIO(select_document[0][0]), mimetype='application/pdf', as_attachment=True,attachment_filename='Report_'+inspection_type+'_'+ hashid + '.pdf')
        else:
            return Response('{"message":"{0} {1} has not {2} in CIDE datatabase"}'.format(inspection_type,inspection_hash,doc_type), mimetype='application/json',status=404)


class DeleteDocument(Resource):
    def __init__(self):
        self.person_class = Person.Person()
        self.connection = pgsql.PGSql()
    

    @auth.verify_password
    def verify_pw(username, password):
        authenticate = authentication.Authentication()
        user = authenticate.verify_user_pass(username, password)
        if not user:
            return False
        g.user = user
        # CHECK IF USER AND ROLES EXIST IN cide_person and cide_role tables, if not create one if yes return OK
        personClass = Person.Person()
        person = personClass.checkLoggedUser(user)
        return True


    def delete_inspection_document(self, document, inspection_type, oid):
    	id_person_role = self.person_class.getPersonRoleId(g.user)
    	id_user = str(id_person_role[0][0][0])
    	#id_user = 100
    	updated_date = datetime.datetime.now().strftime('%Y-%m-%d')
    	if inspection_type == 'specific':
    		table_name = 'cide_specific_inspection'
    		id_collumn = 'id_specific_inspection'
    	else:
    		table_name = 'cide_coordinated_inspection'
    		id_collumn = 'id_coordinated_inspection'
    	SQL = "UPDATE %s SET last_update = %s, id_user %s, %s = %s WHERE %s = %s RETURNING %s"
    	self.connection.connect()
    	update_data = self.connection.query(sql=SQL, data=(table_name,updated_date,id_user,document, None, id_collumn, oid, id_collumn), fetch=False)
    	self.connection.close()
    	return update_data


    def delete(self):
    	doc_type = request.args.get('document')
    	inspection_type = request.args.get('type')
    	inspection_hash = request.args.get('hash')
    	if not doc_type or not inspection_type or not inspection_hash:
    		return Response(status=400)
    	inspection_oid = (hashids.decode(inspection_hash))[0]
    	update_database = self.delete_inspection_document(doc_type, inspection_type, inspection_oid)
    	if update_database:
    		result = '{"updated":"' + hashids.encode(update_database[0][0]) + '"}'
    	else:
    		result = '{"updated": 0}'
    	return Response(result, mimetype='application/json')
