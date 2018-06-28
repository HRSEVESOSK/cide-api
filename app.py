from flask import Flask, render_template, redirect, url_for, request,g
from modules import auth as authentication


app = Flask(__name__)

app.userid = None
app.roles = None

@app.route('/app/home')
def home():
    return render_template('home.html', user=app.userid, roles=app.roles)
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        USER = request.form['username']
        PWD =  request.form['password']
        authenticate = authentication.Authentication()
        loginData = authenticate.verify_user_pass(USER, PWD)
        if loginData:
            user = loginData[0]
            roles = loginData[1]
            if loginData[0] == USER:
                app.userid = user
                app.roles = roles
                return redirect(url_for('home'))
        else:
            error = 'Invalid Credentials. Please try again.'
    return render_template('login.html', error=error)


if __name__ == '__main__':
    loggedUser = None
    app.run(debug=True)
