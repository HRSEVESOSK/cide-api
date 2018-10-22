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
            cide_person = self.connection.query("INSERT INTO cide_person(gs_username) VALUES ('%s') RETURNING id_person" % username,False)
            print("USER CREATED WITH OID: %s" % cide_person[0][0])
        else:
            cide_person = self.connection.query("SELECT id_person FROM cide_person WHERE gs_username = '%s'" % username)
        for role in roles:
            cide_role=self.connection.query("SELECT id_role FROM cide_role WHERE gs_role = '%s'" % role)
            if not cide_role:
                print("ROLE IS \n" + role)
                cide_role = self.connection.query("INSERT INTO cide_role(gs_role) VALUES ('%s') RETURNING id_role" % role,False)
                print("ROLE CREATED WITH OID: %s" % cide_role[0][0])
            #### THE ROLE AND INSPECTION TYPE MATCHING IS BASED ON A VALUE EXTRACTED FROM THE ROLE VALUE ARRAY
            cideroletype = role.split('_')[2]
            id_inspection_type = self.connection.query("SELECT id_inspection_type FROM cide_specific_inspection_type WHERE des_inspection_type LIKE '"+cideroletype+"%'")
            cide_person_role = self.connection.query("SELECT id_person_role FROM cide_person_role WHERE id_person = %s and id_role = %s" % (cide_person[0][0],cide_role[0][0]))
            if not cide_person_role:
                if id_inspection_type:
                    cide_person_role = self.connection.query("INSERT INTO cide_person_role(id_person,id_role,id_inspection_type) VALUES (%s,%s,%s) RETURNING id_person_role" % (cide_person[0][0], cide_role[0][0], id_inspection_type[0][0]), False)
                else:
                    cide_person_role = self.connection.query("INSERT INTO cide_person_role(id_person,id_role) VALUES (%s,%s) RETURNING id_person_role" % (cide_person[0][0], cide_role[0][0]), False)
            if cide_person_role:
                return("CIDE PERSON ROLE AND PERSON_ROLE AVAILABLE WITH ID: %s" % cide_person_role[0][0])
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

