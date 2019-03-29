# -*- coding: utf-8 -*-
from flask_restful import Resource
from flask import Response,request,jsonify
from config import config as cfg
import smtplib
import sys
reload(sys)
sys.setdefaultencoding('utf8')
class Public(Resource):
    def get(self):
        if request.path.endswith('/reset-password'):
            username = request.args.get('uname')
            emAddr=request.args.get('email')
            to = cfg.adminEmails
            subject = '[CIDE-USER-RESET-REQUEST] Request to reset password for username %s' % (username)
            body = 'Dear CIDE Admin, \n\nPlease reset my password for username %s and send the new one to %s. \nBest regards' % (username,emAddr)
            emailBody = "From: %s \nTo: %s \nSubject: %s\n%s" % (cfg.smtpuser, to, subject, body)
            try:
                server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                server.ehlo()
                server.login(cfg.smtpuser, cfg.smtppass)
                server.sendmail(cfg.smtpuser, to, emailBody)
                server.close()
                print 'Email sent!'
                return Response("Email sent to CIDE admin!")
            except:
                print 'Something went wrong...'
                return Response('Something went wrong with email sending to CIDE admin')