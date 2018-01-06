# Copyright 2017 the Isard-vdi project authors:
#      Josep Maria Viñolas Auquer
#      Alberto Larraz Dalmases
# License: AGPLv3

#!flask/bin/python
# coding=utf-8
from flask import render_template, redirect, request, flash, url_for, send_from_directory
#~ from webapp import app
#~ from flask_login import login_required, login_user, logout_user, current_user

#~ from ..auth.authentication import *   
#~ from ..lib.log import *                       

import sys, json, requests, os, time
public_key='$2b$12$LA4uosV80.jkE430c8.wsOI.xIjQ0om7mpQZ0w/G.atH4/83ySTGW'

import rethinkdb as r

import logging as wlog
LOG_LEVEL='INFO'
LOG_FORMAT='%(asctime)s - WIZARD - %(levelname)s: %(message)s'
LOG_DATE_FORMAT='%Y/%m/%d %H:%M:%S'
LOG_LEVEL_NUM = wlog.getLevelName(LOG_LEVEL)
wlog.basicConfig(format=LOG_FORMAT,datefmt=LOG_DATE_FORMAT,level=LOG_LEVEL_NUM)

class Wizard():
    def __init__(self):
        if 'docker' in open('/proc/1/cgroup').read() or True:   
            from flask import Flask
            self.wapp = Flask(__name__)
            
            from ..lib.load_config import loadConfig
            cfg=loadConfig(self.wapp)
            if not cfg.init_app(self.wapp): 
                print('Can not init config on wapp')
                exit(0)
                
            from ..lib.flask_rethink import RethinkDB
            self.db = RethinkDB(self.wapp)
            self.db.init_app(self.wapp)
            if True:
                while not self.check_rethinkdb():
                    wlog.error('No Rethinkdb service')
                    time.sleep(2)
                wlog.info('Rethinkdb service found')
                if not self.check_isard_database():
                    wlog.info('Database not found. Recreating.')
                    self.create_isard_database()
                    
            from ..auth.authentication import Password
            self.pw=Password()
            if not self.check_password():
                from ..lib.isardUpdates import Updates
                self.u=Updates(newapp=self.wapp,newdb=self.db)
                if self.u.isOnline():
                    if self.u.isRegistered():
                        
                        print(self.u.getNewKind('domains','admin'))
                    else:
                        print('is not registeres')
                else:
                    self.u=False
                self.wizard_docker_routes()
                wlog.info('ISARD CONFIGURATION AVAILABLE AT https://localhost')
            
            
                self.wapp.run()
            else:
                self.done_start()

        else:
            self.doWizard=True if self.first_start() else False
            if self.doWizard: # WIZARD WAS FORCED BY DELETING install/.wizard file
                wlog.warning('Starting initial configuration wizard')
                if not self.check_js(first=True):
                    print('Javascript and CSS not installed!')
                    print(' Please install yarn: https://yarnpkg.com/lang/en/docs/install')
                    print(' and run yarn from install folder before starting again.')
                    exit(1)
                try:
                    if self.check_rethinkdb():
                        if not self.check_isard_database():
                            self.create_isard_database()
                        #~ else:
                            #~ self.done_start()
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    log.error(exc_type, fname, exc_tb.tb_lineno)
                    wlog.error(e)
                    None
                self.run_server()
            else: # WIZARD NOT FORCED. SOMETHING IS NOT GOING AS EXPECTED WITH DATABASE?
                if not self.check_rethinkdb():
                    wlog.error('Can not connect to rethinkdb database! Is it running?')
                    exit(1)
                else:
                    if not self.check_isard_database():
                        wlog.error('Database isard not found!')
                        wlog.error('If you need to recreate isard database you should activate wizard again:')
                        wlog.error('   REMOVE install/.wizard file  (rm install/.wizard) and start isard again')
                        exit(1)


    '''
    DOCKER SERVER
    '''
    #~ def register(self):
        #~ try:
            #~ req= requests.post(self.url+'/register' ,allow_redirects=False, verify=False)
            #~ if req.status_code==200:
                #~ with app.app_context():
                    #~ r.table('config').get(1).update({'resources':{'code':req.json()}}).run(db.conn)
                    #~ self.updateFromConfig()
                    #~ return True
            #~ else:
                #~ print('Error response code: '+str(req.status_code)+'\nDetail: '+r.json())
        #~ except Exception as e:
            #~ print("Error contacting.\n"+str(e))
        #~ return False
        
    #~ def resources(self):
        #~ from ..lib.isardUpdates import Updates
        #~ self.u=Updates()
        
    def wizard_docker_routes(self):
        ## Static
        @self.wapp.route('/build/<path:path>')
        def send_build(path):
            return send_from_directory(os.path.join(self.wapp.root_path+'/../', 'bower_components/gentelella/build'), path)
    
        @self.wapp.route('/vendors/<path:path>')
        def send_vendors(path):
            return send_from_directory(os.path.join(self.wapp.root_path+'/../', 'bower_components/gentelella/vendors'), path)

        @self.wapp.route('/', methods=['GET'])
        def docker_base(): 
            #~ self.resources()
            return redirect(url_for('docker_password'))
            
        @self.wapp.route('/wizard_passwd', methods=['GET','POST'])
        def docker_password():  
            print(r.table('users').get('admin').run(self.db.conn))
            if request.method == 'POST':
                if check(r.table('users').get('admin').update({'password':self.pw.encrypt(request.form['password'])}).run(self.db.conn),'replaced'):
                    self.shutdown_server()
                    self.doWizard=False
                    self.done_start()
                    time.sleep(4)
                    return redirect('/admin/updates')
                flash('Something went wrong while trying to update admin password','error')
            return render_template('docker/wizard_pwd.html')

        #~ @self.wapp.route('/wizard_updates', methods=['GET','POST'])
        #~ def docker_updates():  
            #~ try:
                #~ data={}
                #~ data['domains']=
                #~ return json.dumps(u.getNewKind(kind,current_user.id))
            #~ except Exception as e:
                #~ print('exception on read updates: '+str(e))
                #~ return json.dumps([])
                    #~ wlog.info(request.form['passwd'])
            #~ return render_template('docker/wizard_updates.html')
        #~ @app.route('/updates', methods=['GET'])
        #~ def admin_updates():
            #~ return render_template('docker/updates.html', nav="Updates", )

        #~ @app.route('/updates_register', methods=['POST'])
        #~ def admin_updates_register():
            #~ if request.method == 'POST':
                #~ try:
                    #~ if not self.u.isRegistered():
                        #~ self.u.register()
                #~ except Exception as e:
                    #~ log.error('Error registering client: '+str(e))
                    #~ return False
            #~ return True
                    
        #~ @app.route('/updates/<kind>', methods=['GET'])
        #~ def admin_updates_json(kind):
                #~ try:
                    #~ return json.dumps(u.getNewKind(kind,current_user.id))
                #~ except Exception as e:
                    #~ print('exception on read updates: '+str(e))
                    #~ return json.dumps([])

        #~ @app.route('/admin/updates/update/<kind>', methods=['POST'])
        #~ def admin_updates_update(kind):
            #~ if request.method == 'POST':
                #~ data=u.getNewKind(kind,current_user.id)
                #~ if kind == 'domains': 
                    #~ for d in data:
                        #~ d['id']='_'+current_user.id+'_'+d['id']
                        #~ d['percentage']=0
                        #~ d['status']='DownloadStarting'
                        #~ d.update(get_user_data())
                        #~ for disk in d['hardware']['disks']:
                            #~ disk['file']=current_user.path+disk['file']
                #~ elif kind == 'media':
                    #~ for d in data:
                        #~ if 'path' in d.keys():
                            #~ d.update(get_user_data())
                            #~ d['percentage']=0
                            #~ d['status']='DownloadStarting'                    
                            #~ d['path']=current_user.path+d['path']
                #~ app.adminapi.insert_or_update_table_dict(kind,data)
            #~ return json.dumps([])        
            
    '''
    HOST SERVER
    '''
    def run_server(self):
        from flask import Flask
        self.wapp = Flask(__name__)
        self.wizard_routes()
        wlog.info('ISARD WEBCONFIG AVAILABLE AT http://localhost:5000')
        self.wapp.run()        
                
    def shutdown_server(self):
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()
        wlog.info('Stopping wizard flask server')

        
    def first_start(self):
        path='./install/.wizard'
        return True if not os.path.exists(path) else False
            
    def done_start(self):
        path='./install/.wizard'
        try:
            os.mknod(path)
        except:
            None


    def check_js(self,first=False,path='bower_components/gentelella'):
        if first:
            return os.path.exists(os.path.join(os.path.dirname(__file__).rsplit('/',1)[0]+'/'+path))
        return os.path.exists(os.path.join(self.wapp.root_path+'/../',path))
        
    def check_config_file(self):
        path='./isard.conf'
        return False if not os.path.exists(path) else True
        
    def check_config_syntax(self):
        from ..lib.load_config import load_config
        return True if load_config() else False
        
    def check_rethinkdb(self):
        try:
            from ..lib.load_config import load_config
            dict=load_config()
            r.connect(  host=dict['RETHINKDB_HOST'], 
                        port=dict['RETHINKDB_PORT']).repl()
            return True
        except Exception as e:
            wlog.error('Rethinkdb server not found. Is it running? '+str(e))
            #~ wlog.error(e)
            return False

    def check_isard_database(self):
        try:
            if 'isard' in r.db_list().run(): 
                return True
            else:
                return False
        except Exception as e:
            return False

    def check_password(self):
        try:
            #~ pw=Password()
            with self.wapp.app_context():
                usr = r.table('users').get('admin').run(self.db.conn)
                print(usr)
            if usr is None:
                usr = [{'id': 'admin',
                           'name': 'Administrator',
                           'kind': 'local',
                           'active': True,
                           'accessed': time.time(),
                           'username': 'admin',
                           'password': pw.encrypt('isard'),
                           'role': 'admin',
                           'category': 'admin',
                           'group': 'admin',
                           'mail': 'admin@isard.io',
                           'quota': {'domains': {'desktops': 99,
                                                 'desktops_disk_max': 999999999,  # 1TB
                                                 'templates': 99,
                                                 'templates_disk_max': 999999999,
                                                 'running': 99,
                                                 'isos': 99,
                                                 'isos_disk_max': 999999999},
                                     'hardware': {'vcpus': 8,
                                                  'memory': 20000000}},  # 10GB
                           }]
                r.table('users').insert(usr, conflict='update').run(self.db.conn)
                return False # Password must be changed so we return false
            if self.pw.valid('isard',usr['password']):
                print('DEFAULT PASSWORD FOUND')
                return False # Password must be changed
            return True
        except Exception as e:
            print('Check passwd excp: '+str(e))
            return False
        
    def create_isard_database(self):
        from ..config.populate import Populate
        p=Populate()
        if p.database():
            p.defaults()
            return True
        return False

    #~ def check_docker(self):
        #~ # If hypervisor is isard-hypervisor
        
        #~ return False
        
    def check_hypervisor(self):
        # Database hypervisor status
        # options: localhost or isard-hypervisor
        return False
        
    def check_server(self,server):
        import http.client as httplib
        conn = httplib.HTTPConnection(server, timeout=5)
        try:
            conn.request("HEAD", "/")
            conn.close()
            return True
        except Exception as e:
            conn.close()
            return False        

    def check_all(self):
        from ..lib.load_config import load_config
        dict=load_config()
        if dict:
            res  = {'yarn':self.check_js(),
                    'config':True,
                    'config_stx':True,
                    'internet':self.check_server('isardvdi.com'),
                    'rethinkdb':self.check_rethinkdb(),
                    'isard_db':self.check_isard_database(),
                    'passwd':self.check_password(),
                    'docker':True if 'isard-hypervisor' in dict.keys() else False,
                    'hyper':self.check_hypervisor() if self.check_isard_database() else False,
                    'engine':self.check_server('isard-engine:5555' if 'isard-hypervisor' in dict.keys() else 'localhost:5555')}  
        else:
            res =  {'yarn':self.check_js(),
                    'config':self.check_config_file(),
                    'config_stx':self.check_config_syntax(),
                    'internet':self.check_server('isardvdi.com'),
                    'rethinkdb':self.check_rethinkdb(),
                    'isard_db':self.check_isard_database(),
                    'passwd':self.check_password(),
                    'docker':self.check_docker(),
                    'hyper':self.check_hypervisor(),
                    'engine':self.check_engine()}
        res['continue']=res['yarn'] and res['config_stx'] and res['isard_db'] and res['engine']
        return res

    def check_steps(self):
        res = self.check_all()
        errors=[]
        if not res['config'] or not res['config_stx']: 
            errors.append({'stepnum':1,'iserror':True})
        else:
            errors.append({'stepnum':2,'iserror':False})
            
        if not res['rethinkdb'] or not res['isard_db']: 
            errors.append({'stepnum':2,'iserror':True})
        else:
            errors.append({'stepnum':3,'iserror':False})
            
        if not res['passwd']: 
            errors.append({'stepnum':3,'iserror':True})
        else:
            errors.append({'stepnum':3,'iserror':False})
            
        if not res['internet']: 
            errors.append({'stepnum':4,'iserror':True})
        else:
            errors.append({'stepnum':4,'iserror':False})
            
        if not res['engine']: 
            errors.append({'stepnum':5,'iserror':True})
        else:
            errors.append({'stepnum':5,'iserror':False})
            
        if not res['hyper']: 
            errors.append({'stepnum':6,'iserror':True})
        else:
            errors.append({'stepnum':6,'iserror':False})
            
        #~ if res['updates']: errors.append(7)
        return errors
        
    def fake_check_all(self):
        return {'yarn':True,
                'config':False,
                'config_stx':False,
                'internet':False,
                'rethinkdb':False,
                'docker':False,
                'hyper':False,
                'engine':False,
                'isard_db':False,
                'continue':True}
                
    def get_isardvdi_resources():
        None
    
    def wizard_routes(self):
            # Static
            @self.wapp.route('/build/<path:path>')
            def send_build(path):
                return send_from_directory(os.path.join(self.wapp.root_path+'/../', 'bower_components/gentelella/build'), path)
    
            @self.wapp.route('/vendors/<path:path>')
            def send_vendors(path):
                return send_from_directory(os.path.join(self.wapp.root_path+'/../', 'bower_components/gentelella/vendors'), path)

            @self.wapp.route('/errors', methods=['POST'])
            def errors():
                return json.dumps(self.check_steps())
                
            @self.wapp.route('/', methods=['GET'])
            def base():
                #~ chk=self.check_all()
                chk=self.fake_check_all()
                msg=''
                if not chk['yarn']:
                    msg='Javascript and CSS libraries not found. Please install it running yarn on install folder.'
                    return render_template('missing_yarn.html',chk=chk, msg=msg.split('\n'))
                return render_template('wizard_main.html',chk=chk, msg=msg.split('\n'))
                if not chk['config']:
                    msg+='\nIsard main configuration file isard.conf missing. Please copy (or rename) isard.conf.default to isard.conf.'
                    return render_template('missing_config.html',chk=chk, msg=msg.split('\n'))
                if not chk['config_stx']:
                    msg+='\nMain configuration file isard.conf can not be read. Please check configuration from isard.conf.default.'
                    return render_template('missing_config.html',chk=chk, msg=msg.split('\n'))
                if not chk['rethinkdb']:
                    msg+='\nUnable to connect to Rethinkdb server using isard.conf parameters. Is RethinkDB service running?'
                    return render_template('missing_db.html',chk=chk, msg=msg.split('\n'))
                if not chk['isard_db']:
                    msg+='\nRethinkDb isard database not found on server. You should create it now.'
                    return render_template('missing_db.html',chk=chk, msg=msg.split('\n'))
                if not chk['internet']:
                    msg+='\nCan not reach Internet. Please check your Internet connection.'
                #~ msg='Everything seems ok. You can continue'
                return render_template('missing_yarn.html',chk=chk, msg=msg.split('\n'))
    
            # Flask routes
            @self.wapp.route('/create_db', methods=['GET'])
            def wizard_createdb():
                return self.create_isard_database()

            @self.wapp.route('/passwd', methods=['GET','POST'])
            def wizard_passwd():
                if request.method == 'POST':
                    wlog.info(request.form['passwd'])
                return render_template('wizard_pwd.html')

            @self.wapp.route('/shutdown', methods=['GET'])
            def wizard_shutdown():
                # This shutdowns wizard flask server and allows for main isard src to continue loading.
                self.shutdown_server()
                self.doWizard=False
                time.sleep(4)
                return redirect('/')




            @self.wapp.route('/validate/<step>', methods=['POST'])
            def wizard_validate_step(step):
                print('im on step '+step)
                if request.method == 'POST':
                    if step is '1':
                        return self.check_config_file() and self.check_config_syntax()
                    if step is '2':
                        return self.check_rethinkdb() and self.check_isard_database()
                                            
            @self.wapp.route('/content', methods=['POST'])
            def wizard_content():
                global html
                if request.method == 'POST':
                    step=request.form['step_number']
                    print(step)
                    if step == '1':
                        print('step 1')
                        if not self.check_config_file():
                            return html[1]['noconfig']
                        elif not self.check_config_syntax():
                            return html[1]['nosyntax']
                        return html[1]['ok']
                    if step == '2':
                        return 'step2'
                    #~ step=request.get_json(force=True)['step_number']
                    #~ import random
                    #~ rand=random.random() * 100
                    #~ return html[1]['ko'].replace('%step%',str(rand))
                    


html={}                    
html[1]={'ok': '''<h2 class="StepTitle">Step 1. Configuration</h2>
                <h3>Configuration file found and correct<h3>''',
        'noconfig': '''<h2 class="StepTitle">Step 1. Configuration</h2>
                <h3>Configuration file not found<h3>
                <p>Do you want to use the default configuration found?<p>
                <button type="config-copy" class="btn btn-default submit">Fix</button>''',
        'nosyntax': '''<h2 class="StepTitle">Step 1. Configuration</h2>
                <h3>Configuration file has incorrect syntax.<h3>
                <p>Please review sample isard.conf.default file and update
                your isard.conf file accordingly<p>'''}
        
        



def check(dict,action):
    #~ These are the actions:
    #~ {u'skipped': 0, u'deleted': 1, u'unchanged': 0, u'errors': 0, u'replaced': 0, u'inserted': 0}
    if dict[action]: 
        return True
    if not dict['errors']: return True
    return False
