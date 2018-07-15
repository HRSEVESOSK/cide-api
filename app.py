import os,json,requests
from flask import Flask, render_template, redirect, url_for, request,g,session
from modules import auth as authentication
from config import config as cfg
from flask_basicauth import BasicAuth
from functools import wraps

app = Flask(__name__)

app.userid = None
app.userpwd = None
app.roles = None

app.config['BASIC_AUTH_USERNAME'] = ''
app.config['BASIC_AUTH_PASSWORD'] = ''
basic_auth = BasicAuth(app)

app.apiURL = 'http://localhost:5001/api'

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        authenticate = authentication.Authentication()
        if not auth or not authenticate.verify_user_pass(auth.username, auth.password):
            return login()
        return f(*args, **kwargs)
    return decorated

@app.route('/app')
def home():
    print("AUTH USER: %s " % app.userid)
    print("AUTH PASS: %s " % app.userpwd)
    print("AUTH ROLES: %s" % app.roles)
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        return render_template('home.html',user=app.userid,roles=app.roles )

@app.route('/app/inspection/<id>')
#CHECK HO TO MAKE VERIFICATION
#@basic_auth.required()
def getCoordInspByEstaId(id):
    print("AUTH USER: %s " % app.userid)
    print("AUTH PASS: %s " % app.userpwd)
    print("AUTH ROLES: %s" % app.roles)
    print(app.config['BASIC_AUTH_USERNAME'])
    url = app.apiURL + '/inspection/' + id
    response = requests.get(url, auth=(app.userid, app.userpwd))
    return json.dumps(response.json())


@app.route('/app/search', methods=['GET'])
#@requires_auth
#@basic_auth.check_credentials(loggedUser)
def estabData():
    print("AUTH USER: %s " % app.userid)
    print("AUTH PASS: %s " % app.userpwd)
    url = app.apiURL + '/establishment'
    headers = {'Content-Type': 'application/json'}
    if request.args.get('q') == '':
        params = ''
    elif request.args.get('q')[0].isdigit():
        params = 'oib=' + request.args.get('q')
    else:
        params = 'name=' + request.args.get('q')
    response = requests.get(url, params=params, auth=(app.userid, app.userpwd))
    print params
    if response.status_code == 200:
        if not response.json():
            return "No results matching query: " + params
        else:
            return render_template('establishment.html', entries=response.json())

    elif response.status_code == 401:
        return redirect(url_for('login'))
@app.route('/app/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        USER = request.form['username']
        PWD =  request.form['password']
        print("SENDING UNAME: " + USER)
        print("SENDING PASS: " + PWD)
        authenticate = authentication.Authentication()
        loginData = authenticate.verify_user_pass(USER, PWD)
        if loginData:
            user = loginData[0]
            roles = loginData[1]
            if loginData[0] == USER:
                app.config['BASIC_AUTH_USERNAME'] = USER
                app.config['BASIC_AUTH_PASSWORD'] = PWD
                app.userid = user
                app.roles = roles
                app.userpwd = PWD
                session['logged_in'] = True
                session['user'] = user
                session['roles'] = roles
                g.user = user[0]
                return redirect(url_for('home'))
        else:
            error = 'Invalid Credentials. Please try again.'
    return render_template('login.html', error=error)

@app.route("/app/logout")
def logout():
    session['logged_in'] = False
    return home()

if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    loggedUser = None
    app.run(debug=True,host=cfg.host,port=cfg.appport)
