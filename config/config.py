namespace = 'KLIMETO'
localhost = True
development = False
if localhost:
    host = 'localhost'
    appport = '5000'
    apiport = '5001'
    dbhost = "193.37.152.219"
    dbport = "5432"
    dbname = "cidedb"
    dbuser = "cideuser"
    dbpwd = "cidepwd"
    tempDataDir = '/scratch/cide-app/temp'
    logsDir = '/scratch/cide-app/logs'
    debug = True
elif development:
    host = '192.168.1.66'
    port = '5000'
    dbhost = "192.168.1.226"
    dbport = "5432"
    dbname = "BIFISIC"
    dbuser = "bifisic"
    dbpwd = "mypass"
    tempDataDir = '/scratch/cide-app/temp'
    logsDir = '/scratch/cide-app/logs'
    debug = True
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