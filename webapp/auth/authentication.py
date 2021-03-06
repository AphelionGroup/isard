# Copyright 2017 the Isard-vdi project authors:
#      Josep Maria Viñolas Auquer
#      Alberto Larraz Dalmases
# License: AGPLv3

#!/usr/bin/env python
# coding=utf-8
import rethinkdb as r
from flask_login import LoginManager, UserMixin
import time

from webapp import app
from ..lib.flask_rethink import RethinkDB

db = RethinkDB(app)
db.init_app(app)
from ..lib.log import *

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

ram_users={}

class LocalUsers():
    def __init__(self):
        None
    
    def getUser(self,username):
        with app.app_context():
            usr=r.table('users').get(username).run(db.conn)
        return usr

class User(UserMixin):
    def __init__(self, dict):
        self.id = dict['id']
        self.username = dict['id']
        self.name = dict['name']
        self.password = dict['password']
        self.role = dict['role']
        self.category = dict['category']
        self.group = dict['group']
        self.path = dict['category']+'/'+dict['group']+'/'+dict['id']+'/'
        self.mail = dict['mail']
        self.quota = dict['quota']
        self.is_admin=True if self.role=='admin' else False
        self.active = dict['active']

    def is_active(self):
        return self.active
    
    def is_anonymous(self):
        return False

def logout_ram_user(username):
    del(ram_users[username])
             
@login_manager.user_loader
def user_loader(username):
    if username not in ram_users:
        user=app.localuser.getUser(username)
        if user is None: return
        ram_users[username]=user
    return User(ram_users[username])

'''
LOCAL AUTHENTICATION AGAINS RETHINKDB USERS TABLE
'''
try:
    import ldap
except Exception as e:
    log.warning('No ldap module found, disabling ldap authentication')
    
from ..config.ldapauth import myLdapAuth
class auth(object):
    def __init__(self):
        None


    def fakecheck(self,fakeuser,admin_password):
        return self.authentication_fakeadmin(fakeuser,admin_password)
        
          
    def check(self,username,password):
        if username=='admin':
            user_validated=self.authentication_local(username,password)
            if user_validated:
                self.update_access(username)
                return user_validated
        with app.app_context():
            cfg=r.table('config').get(1).run(db.conn)
        if cfg is None:
            return False
        ldap_auth=cfg['auth']['ldap']
        local_auth=cfg['auth']['local']
        local_user=r.table('users').get(username).run(db.conn)
        if local_user is not None:
            if local_user['kind']=='local' and local_auth['active']:
                user_validated = self.authentication_local(username,password)
                if user_validated:
                    self.update_access(username)
                    return user_validated
            if local_user['kind']=='ldap' and ldap_auth['active']:
                user_validated = self.authentication_ldap(username,password)
                if user_validated:
                    self.update_access(username)
                    return user_validated
            #~ if local_user['kind']=='google_oauth2':
                #~ return self.authentication_googleOauth2(username,password)
        else:
            if ldap_auth['active']:
                user_validated=self.authentication_ldap(username,password)
                if user_validated:
                    user=self.authentication_ldap(username,password,returnObject=False)
                    if r.table('categories').get(user['category']).run(db.conn) is None:
                        r.table('categories').insert({  'id':user['category'],
                                                        'name':user['category'],
                                                        'description':'',
                                                        'quota':r.table('roles').get(user['role']).run(db.conn)['quota']}).run(db.conn)
                    if r.table('groups').get(user['group']).run(db.conn) is None:
                        r.table('groups').insert({  'id':user['group'],
                                                        'name':user['group'],
                                                        'description':'',
                                                        'quota':r.table('categories').get(user['category']).run(db.conn)['quota']}).run(db.conn)
                    r.table('users').insert(user).run(db.conn)
                    self.update_access(username)
                    return User(user)
                else:
                    return False
        return False
        
    def authentication_local(self,username,password):
        with app.app_context():
            dbuser=r.table('users').get(username).run(db.conn)
            log.info('USER:'+username)
            if dbuser is None:
                return False
        pw=Password()
        if pw.valid(password,dbuser['password']):
            #~ TODO: Check active or not user
            return User(dbuser)
        else:
            return False
   

    def authentication_ldap(self,username,password,returnObject=True):
        cfg=r.table('config').get(1).run(db.conn)['auth']
        try:
            conn = ldap.initialize(cfg['ldap']['ldap_server'])
            id_conn = conn.search(cfg['ldap']['bind_dn'],ldap.SCOPE_SUBTREE,"uid=%s" % username)
            tmp,info=conn.result(id_conn, 0)
            user_dn=info[0][0]
            if conn.simple_bind_s(who=user_dn,cred=password):
                '''
                config/ldapauth.py has the function you can change to adapt to your ldap
                '''
                au=myLdapAuth()
                newUser=au.newUser(username,info[0])
                return User(newUser) if returnObject else newUser
            else:
                return False
        except Exception as e:
            log.error("LDAP ERROR:",e)
            return False
            
    def authentication_fakeadmin(self,fakeuser,admin_password):
        with app.app_context():
            admin_dbuser=r.table('users').get('admin').run(db.conn)
            if admin_dbuser is None:
                return False
        pw=Password()
        if pw.valid(admin_password,admin_dbuser['password']):
            with app.app_context():
                dbuser=r.table('users').get(fakeuser).run(db.conn)
            if dbuser is None:
                return False
            else:
                dbuser['name']='FAKEUSER'
                #~ quota = admin_dbuser['quota']
                #~ {  'domains':{ 'desktops': 99,
                                                #~ 'templates':99,
                                                #~ 'running':  99},
                                    #~ 'hardware':{'vcpus':    8,
                                                #~ 'ram':      1000000}} # 10GB
                dbuser['quota']=admin_dbuser['quota']
                dbuser['role']='admin'
                ram_users[fakeuser]=dbuser
                return User(dbuser)
        else:
            return False   
   
    def update_access(self,username):
        with app.app_context():
            r.table('users').get(username).update({'accessed':time.time()}).run(db.conn)

    def ldap_users_exists(self,commit=False):
        cfg=r.table('config').get(1).run(db.conn)['auth']
        users=list(r.table('users').filter({'active':True,'kind':'ldap'}).pluck('id','name','accessed').run(db.conn))
        nonvalid=[]
        valid=[]
        for u in users:
            conn = ldap.initialize(cfg['ldap']['ldap_server'])
            id_conn = conn.search(cfg['ldap']['bind_dn'],ldap.SCOPE_SUBTREE,"uid=%s" % u['id'])
            tmp,info=conn.result(id_conn, 0)
            if len(info):
                valid.append(u)
            else:
                nonvalid.append(u)
        if commit:
            nonvalid_list= [ u['id'] for u in nonvalid ]
            return r.table('users').get_all(r.args(nonvalid_list)).update({'active':False}).run(db.conn)
        else:
            return {'nonvalid':nonvalid,'valid':valid}
        #~ print(nonvalid)
        #~ print('Non valids: '+str(len(nonvalid)))
        #~ print('Valids: '+str(len(valid)))
   
'''
VOUCHER AUTH
'''         
import smtplib
class Email(object):
    def __init__(self):
        try:
            self.passwd=os.environ.get('ISARDMAILKEY')
        except Exception as e:
            print('Environtment email password not found.')
        
    def send(self,to_addr_list,subject,message):
        login = 'isard.vdi@gmail.com'
        # In bash do: export ISARDMAILKEY=some_value
        password = os.environ.get('ISARDMAILKEY')
        smtpserver='smtp.gmail.com'
        smtpport=587
        from_addr='isard.vdi@gmail.com'
        subject=subject
        message=message
        header  = 'From: %s\n' % from_addr
        header += 'To: %s\n' % ','.join(to_addr_list)
        # header += 'Cc: %s\n' % ','.join(cc_addr_list)
        header += 'Subject: %s\n\n' % subject
        message = header + message

        server = smtplib.SMTP(smtpserver, smtpport)  # use both smtpserver  and -port
        server.starttls()
        server.login(login,password)
        problems = server.sendmail(from_addr, to_addr_list, message)
        server.quit()
        #~ print 'Sent email: '+error_header

    def email_validation(self,email,code):
        subject= 'IsardVDI email verification'
        message= 'You have requested access to IsardVDI online demo platform through this email address.\n\n'+\
                 'Please access this link to get your demo user: https://try.isardvdi.com/voucher_validation/'+code
        self.send([email],subject,message)

    def account_activation(self,email,user,passwd):
        subject= 'IsardVDI credentials'
        message= 'Here you have your demo user and passwords: \n\n'+\
                 'Username: '+user+'\n'+\
                 'Password: '+passwd+'\n\n'+\
                 'IsardVDI:  https://try.isardvdi.com'
        self.send([email],subject,message)        
        
class auth_voucher(object):
    def __init__(self):
        self.pw=Password()
        self.email=Email()

    def check_voucher(self,voucher):
        dbv=r.table('vouchers').get(voucher).run(db.conn)
        if dbv is None: return False
        return True

    def check_validation(self,code):
        user=list(r.table('users').filter({'code':code}).run(db.conn))
        if not len(user): return False
        return True
        
    def check_user_exists(self,email):
        user=r.table('users').get(email).run(db.conn)
        if user is None: return False
        return True
                
    def register_user(self,voucher,email,remote_addr):
        user=self.user_tmpl(voucher,email,remote_addr)
        if r.table('categories').get(user['category']).run(db.conn) is None:
                r.table('categories').insert({  'id':user['category'],
                                                'name':user['category'],
                                                'description':'',
                                                'quota':r.table('roles').get(user['role']).run(db.conn)['quota']}).run(db.conn)
        if r.table('groups').get(user['group']).run(db.conn) is None:
                r.table('groups').insert({  'id':user['group'],
                                            'name':user['group'],
                                            'description':'',
                                            'quota':r.table('categories').get(user['category']).run(db.conn)['quota']}).run(db.conn)
        r.table('users').insert(user, conflict='update').run(db.conn)
        
        # Send email with code=user['code']        
        self.email.email_validation(email,user['code'])  
        return User(user)  
        #~ return False

    def activate_user(self,code,remote_addr):
        user=list(r.table('users').filter({'code':code}).run(db.conn))
        if len(user):
            user=user[0]
            key=self.pw.generate_human()
            r.table('users').filter({'code':code}).update({'active':True,'password':self.pw.encrypt(key)}).run(db.conn)
            log=list(r.table('users').filter({'code':code}).run(db.conn))[0]['log']
            log.append({'when':time.time(),'ip':remote_addr,'action':'Activate user'})
            r.table('users').filter({'code':code}).update({'log':log}).run(db.conn)
            #Send mail with email=user['mail'], user=user['username'], key
            self.email.account_activation(user['mail'], user['username'], key)
            return True
        return False
        
    def user_tmpl(self,voucher, email, remote_addr):
        usr = {'id': email.replace('@','_').replace('.','_'),
                'name': email.split('@')[0],
                'kind': 'local',
                'active': False,
                'accessed': time.time(),
                'username': email.replace('@','_').replace('.','_'),
                'password': self.pw.encrypt(self.pw.generate_human()), #Unknown temporary key, updated on activate_user
                'code': self.pw.encrypt(self.pw.generate_human()).replace('/','-').replace('.','_'), # Code for mail confirmation
                'log':[{'when':time.time(),'ip':remote_addr,'action':'Register user'}],
                'role': 'advanced',
                'category': voucher,
                'group': voucher,
                'mail': email,
                'quota': {'domains': {'desktops': 3,
                                        'desktops_disk_max': 999999999,  # 1TB
                                        'templates': 2,
                                        'templates_disk_max': 999999999,
                                        'running': 1,
                                        'isos': 1,
                                        'isos_disk_max': 999999999},
                                        'hardware': {'vcpus': 2,
                                                    'memory': 20000000}},  # 2GB
                }
        r.table('users').insert(usr, conflict='update').run(db.conn)
        return usr

    def update_access(self,username):
        with app.app_context():
            r.table('users').get(username).update({'accessed':time.time()}).run(db.conn)        
        
'''
PASSWORDS MANAGER
'''
import bcrypt,string,random
class Password(object):
        def __init__(self):
            None

        def valid(self,plain_password,enc_password):
            return bcrypt.checkpw(plain_password.encode('utf-8'), enc_password.encode('utf-8'))
                
        def encrypt(self,plain_password):
            return bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        def generate_human(self,length=6):
            chars = string.ascii_letters + string.digits + '!@#$*'
            rnd = random.SystemRandom()
            return ''.join(rnd.choice(chars) for i in range(length))
        
