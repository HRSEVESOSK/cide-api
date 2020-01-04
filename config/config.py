namespace = 'AZO'
localhost = True
development = False
siroles = ['ROLE_CIDE_EL',
           'ROLE_CIDE_ENV',
           'ROLE_CIDE_EONTO',
           'ROLE_CIDE_ICZ',
           'ROLE_CIDE_IED',
           'ROLE_CIDE_IGOK',
           'ROLE_CIDE_IZS',
           'ROLE_CIDE_OPT',
           'ROLE_CIDE_POLJ',
           'ROLE_CIDE_PRI',
           'ROLE_CIDE_RUD',
           'ROLE_CIDE_SAN',
           'ROLE_CIDE_STO',
           'ROLE_CIDE_VET',
           'ROLE_CIDE_VOD',
           'ROLE_CIDE_ZNR',
           'ROLE_CIDE_ZP']
if namespace == 'AZO':
    if localhost:
        host = 'localhost'
        appport = '5000'
        apiport = '5001'
        dbhost = "192.168.1.226"
        dbport = "5432"
        dbname = "BIFISIC"
        dbuser = "bifisic"
        dbpwd = "mypass"
        tempDataDir = 'data/upload'
        extensions = ['pdf']
        logsDir = 'logs'
        debug = True
        authapi = 'http://192.168.1.226/bifisic/services/httpbasicauth/auth'
        #authapi = 'https://pproo.azo.hr/bifisic/services/httpbasicauth/auth'
    elif development:
        host = '192.168.1.77'
        appport = '80'
        apiport = '8080'
        dbhost = "192.168.1.226"
        dbport = "5432"
        dbname = "BIFISIC"
        dbuser = "bifisic"
        dbpwd = "mypass"
        tempDataDir = 'data\upload'
        extensions = ['pdf','doc','docx']
        logsDir = 'logs'
        debug = True
        authapi = 'http://192.168.1.226/bifisic/services/httpbasicauth/auth'
    else:
        host = 'http://pproo.azo.hr/cide'
        port = '80'
        dbhost = "localhost"
        dbport = "5432"
        dbname = "BIFISIC"
        dbuser = "bifisic"
        dbpwd = "mypass"
        tempDataDir = '/scratch/cide/temp'
        logsDir = '/scratch/cide/logs'
        debug = False
        authapi = 'https://pproo.azo.hr/bifisic/services/httpbasicauth/auth'
