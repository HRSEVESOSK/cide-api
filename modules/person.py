import lib.pgsql as pgsql
class Person():
    def __init__(self):
        self.connection = pgsql.PGSql()
    def checkLoggedUser(self,user):
        username = user[0]
        roles = user[1]
        SQL="SELECT id_person FROM cide_person WHERE gs_username=%s"
        self.connection.connect()
        user_exists = self.connection.query(sql=SQL,data=[username])
        self.connection.close()
        if not user_exists:
            print("USERNAME IS \n" + username)
            SQL="INSERT INTO cide_person(gs_username) VALUES (%s) RETURNING id_person"
            self.connection.connect()
            cide_person = self.connection.query(sql=SQL,data=[username],fetch=False)
            self.connection.close()
            print("USER CREATED WITH OID: %s" % cide_person[0][0])
        else:
            SQL="SELECT id_person FROM cide_person WHERE gs_username=%s"
            self.connection.connect()
            cide_person = self.connection.query(sql=SQL,data=[username])
            self.connection.close()
        for role in roles:
            SQL="SELECT id_role FROM cide_role WHERE gs_role = %s"
            self.connection.connect()
            cide_role = self.connection.query(sql=SQL,data=[role])
            self.connection.close()
            if not cide_role:
                print("ROLE IS \n" + role)
                SQL = "INSERT INTO cide_role(gs_role) VALUES (%s) RETURNING id_role"
                self.connection.connect()
                cide_role = self.connection.query(sql=SQL,data=[role],fetch=False)
                self.connection.close()
                print("ROLE CREATED WITH OID: %s" % cide_role[0][0])
            #### THE ROLE AND INSPECTION TYPE MATCHING IS BASED ON A VALUE EXTRACTED FROM THE ROLE VALUE ARRAY
            cide_role_type = role.split('_')[2]
            SQL="SELECT id_inspection_type FROM cide_specific_inspection_type WHERE des_inspection_type LIKE %s"
            self.connection.connect()
            id_inspection_type = self.connection.query(sql=SQL,data=[cide_role_type+'%'])
            self.connection.close()
            SQL="SELECT id_person_role FROM cide_person_role WHERE id_person = %s and id_role = %s"
            self.connection.connect()
            cide_person_role = self.connection.query(sql=SQL,data=(cide_person[0][0],cide_role[0][0]))
            self.connection.close()
            if not cide_person_role:
                if id_inspection_type:
                    SQL="INSERT INTO cide_person_role(id_person,id_role,id_inspection_type) VALUES (%s,%s,%s) RETURNING id_person_role"
                    self.connection.connect()
                    cide_person_role = self.connection.query(sql=SQL,data=(cide_person[0][0], cide_role[0][0], id_inspection_type[0][0]), fetch=False)
                    self.connection.close()
                else:
                    SQL="INSERT INTO cide_person_role(id_person,id_role) VALUES (%s,%s) RETURNING id_person_role"
                    self.connection.connect()
                    cide_person_role = self.connection.query(sql=SQL, data=(cide_person[0][0], cide_role[0][0]), fetch=False)
                    self.connection.close()
            if cide_person_role:
                return("CIDE PERSON ROLE AND PERSON_ROLE AVAILABLE WITH ID: %s" % cide_person_role[0][0])
        else:
            return("CIDE PERSON ALREADY EXISTS")

    def getPersonRoleId(self,user):
        self.connection.connect()
        username = user[0]
        ## THIS IS HARD CODED TO FIRST VALUES IN ROLES ARRAY, TO BE CHECKED WHAT IF A USER HAS MORE ROLES!!!
        role = user[1][0]
        SQL="SELECT id_person FROM cide_person WHERE gs_username=%s"
        self.connection.connect()
        id_person=self.connection.query(sql=SQL,data=[username])
        self.connection.close()
        SQL="SELECT id_role FROM cide_role WHERE gs_role=%s"
        self.connection.connect()
        id_role = self.connection.query(sql=SQL,data=[role])
        self.connection.close()
        if id_person and id_role:
            SQL="SELECT id_person_role FROM cide_person_role WHERE id_person = %s AND id_role = %s"
            self.connection.connect()
            id_person_role = self.connection.query(sql=SQL,data=(id_person[0][0],id_role[0][0]))
            self.connection.close()
        return id_person,id_role,id_person_role

