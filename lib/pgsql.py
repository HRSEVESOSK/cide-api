import psycopg2, logging
import psycopg2.extras

from config import config as cfg

class PGSql:
    def __init__(self):
        self.dsn = None  # "host='%s' port='%s' dbname='%s' user='%s' password='%s'" % (cfg.dbhost, cfg.dbport, cfg.dbname, cfg.dbuser, cfg.dbpwd)
        self.dsn = "host='%s' port='%s' dbname='%s' user='%s' password='%s'" % (cfg.dbhost, cfg.dbport, cfg.dbname, cfg.dbuser, cfg.dbpwd)
        self.Err = None
        self.numresult = 0

    def setDsn(self, dsn):
        self.dsn = dsn

    def connect(self):
        # type: () -> object
        """ Connect to PG """
        try:
            self.conn = psycopg2.connect(self.dsn,cursor_factory=psycopg2.extras.DictCursor)
        except StandardError, err:
            print ("Could not connect to DB \n  %s" % err)
            return False

    def close(self):
        """ Close DB connection """
        self.conn.close()

    def query(self, sql, fetch=True):
        print("Function query was called")
        logging.info("Function query was called")
        #print("Function query was called for '%s'" % sql[0:250])
        logging.info("Function query was called for '%s'" % sql[0:100])
        """ Execute query """
        try:
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        except StandardError, err:
            print ("could not establish cursor on connection \n   %s" % err)
            logging.error("could not establish cursor on connection \n   %s" % err)
            return False

        try:
            cur.execute(sql)
            # print ("SUCCESS executing: %s \n  " % (sql))
        except StandardError, err:
            print ("ERROR executing SQL query:  %s" % (err))
            logging.error("ERROR executing SQL query:  %s" % (err))
            return False

        if fetch:
            self.numresult = cur.rowcount
            print("NUMBER OF RESULTS")
            print self.numresult
            result = cur.fetchall()
            return result
        else:
            self.conn.commit()
            try:
                result = cur.fetchall()
                return result
            except psycopg2.ProgrammingError:
                return True
            '''
            if type(cur.fetchall()) is list:
                result = cur.fetchall()
                return result
            else:
               return True
            '''

    def fetchAll(self, sql):
        self.connect()
        result = self.query(sql)
        self.close()
        return result

    def getErr(self):
        return self.Err

    def getNumresult(self):
        return self.numresult