import lib.pgsql as pgsql
class Person():
    def __init__(self):
        self.connection = pgsql.PGSql()
    def checkLoggedUser(self,user):
        username = user[0]
        roles = user[1]
        self.connection.connect()
        userexists = self.connection.query("SELECT id_person FROM cide_person WHERE gs_username = '%s'" % username)
        if not userexists:
            print("USERNAME IS \n" + username)
            createuser = self.connection.query("INSERT INTO cide_person(gs_username) VALUES ('%s') RETURNING id_person" % username,False)
            print("USER CREATED WITH OID: %s" % createuser[0][0])
        for role in roles:
            roleexists=self.connection.query("SELECT id_role FROM cide_role WHERE gs_role = '%s'" % role)
            if not roleexists:
                print("ROLE IS \n" + role)
                createrole = self.connection.query("INSERT INTO cide_role(gs_role) VALUES ('%s') RETURNING id_role" % role,False)
                print("ROLE CREATED WITH OID: %s" % createrole[0][0])
                cideroletype = role.split('_')[2]
                id_inspection_type = self.connection.query("SELECT id_inspection_type FROM cide_specific_inspection_type WHERE des_inspection_type LIKE '"+cideroletype+"%'")
                if id_inspection_type:
                    createpersonrole = self.connection.query("INSERT INTO cide_person_role(id_person,id_role,id_inspection_type) VALUES (%s,%s,%s) RETURNING id_person_role" % (createuser[0][0], createrole[0][0], id_inspection_type[0][0]), False)
                else:
                    createpersonrole = self.connection.query("INSERT INTO cide_person_role(id_person,id_role) VALUES (%s,%s) RETURNING id_person_role" % (createuser[0][0], createrole[0][0]), False)
                if createpersonrole:
                    return("CIDE PERSON AND ROLE CREATED")
            self.connection.close()
        else:
            return("CIDE PERSON ALREADY EXISTS")

    def getPersonRoleId(self,user):
        self.connection.connect()
        username = user[0]
        ## THIS IS HARD CODED TO FIRST VALUES IN ROLES ARRAY, TO BE CHECKED WHAT IF A USER HAS MORE ROLES!!!
        role = user[1][0]
        idperson = self.connection.query("SELECT id_person FROM cide_person WHERE gs_username = '%s'" % username)
        idrole = self.connection.query("SELECT id_role FROM cide_role WHERE gs_role = '%s'" % role)
        if idperson and idrole:
            idpersonrole = self.connection.query("SELECT id_person_role FROM cide_person_role WHERE id_person = %s AND id_role = %s" % (idperson[0][0],idrole[0][0]))
        return idperson,idrole,idpersonrole

