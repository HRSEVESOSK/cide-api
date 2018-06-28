development = True
if development:
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