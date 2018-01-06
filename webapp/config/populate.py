# Copyright 2017 the Isard-vdi project authors:
#      Josep Maria Viñolas Auquer
#      Alberto Larraz Dalmases
# License: AGPLv3

#!/usr/bin/env python
# coding=utf-8

import rethinkdb as r
import time
#~ from webapp import app
#~ from ..lib.flask_rethink import RethinkDB
from ..lib.log import *
import sys
#~ db = RethinkDB(app)
#~ db.init_app(app)

from ..auth.authentication import Password

from ..lib.load_config import load_config


class Populate(object):
    def __init__(self):
        self.cfg=load_config()
        try:
            self.conn = r.connect( self.cfg['RETHINKDB_HOST'],self.cfg['RETHINKDB_PORT'],self.cfg['RETHINKDB_DB']).repl()
        except Exception as e:
            None
        self.p = Password()
        self.passwd = self.p.encrypt('isard')
        
    '''
    DATABASE
    '''

    def database(self):
        try:
            #~ with app.app_context():
                if not r.db_list().contains(self.cfg['RETHINKDB_DB']).run():
                    log.warning('Database {} not found, creating new one.'.format(self.cfg['RETHINKDB_DB']))
                    r.db_create(self.cfg['RETHINKDB_DB']).run()
                    return 1
                log.info('Database {} found.'.format(self.cfg['RETHINKDB_DB']))
                return 2
        except Exception as e:
            #~ exc_type, exc_obj, exc_tb = sys.exc_info()
            #~ fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            #~ log.error(exc_type, fname, exc_tb.tb_lineno)
            log.error('Can not connect to rethinkdb database! Is it running on HOST:'+self.cfg['RETHINKDB_HOST']+' PORT:'+self.cfg['RETHINKDB_PORT']+' DB:'+self.cfg['RETHINKDB_DB']+' ??')
            return False


    def defaults(self):
        log.info('Checking table roles')
        self.roles()
        log.info('Checking table categories')
        self.categories()
        log.info('Checking table groups')
        self.groups()
        log.info('Checking table users')
        self.users()
        log.info('Checking table vouchers')
        self.vouchers()
        log.info('Checking table hypervisors and pools')
        self.hypervisors()
        log.info('Checking table interfaces')
        self.interfaces()
        log.info('Checking table graphics')
        self.graphics()
        log.info('Checking table videos')
        self.videos()
        log.info('Checking table disks')
        self.disks()
        log.info('Checking table domains')
        self.domains()
        log.info('Checking table domains_status')
        self.domains_status()
        log.info('Checking table virt_builder')
        self.virt_builder()
        log.info('Checking table virt_install')
        self.virt_install()
        log.info('Checking table builders')
        self.builders()
        log.info('Checking table media')
        self.media()
        log.info('Checking table boots')
        self.boots()
        log.info('Checking table hypervisors_events')
        self.hypervisors_events()
        log.info('Checking table hypervisors_status')
        self.hypervisors_status()
        log.info('Checking table disk_operations')
        self.disk_operations()
        log.info('Checking table hosts_viewers')
        self.hosts_viewers()
        log.info('Checking table places')
        self.places()
        log.info('Checking table disposables')
        self.disposables()
        log.info('Checking table backups')
        self.backups()
        log.info('Checking table config')
        self.config()

    '''
    CONFIG
    '''

    def config(self):
        with app.app_context():
            if not r.table_list().contains('config').run():
                log.warning("Table config not found, creating new one.")
                r.table_create('config', primary_key='id').run()
                self.result(r.table('config').insert([{'id': 1,
                                                       'auth': {'local': {'active': True},
                                                                'ldap': {'active': False,
                                                                         'ldap_server': 'ldap://ldap.domain.org',
                                                                         'bind_dn': 'dc=domain,dc=org'}},
                                                        'disposable_desktops':{'active': False},
                                                        'voucher_access':{'active': False},
                                                        'engine':{  'intervals':{   'status_polling':10,
                                                                                    'time_between_polling': 5,
                                                                                    'test_hyp_fail': 20,
                                                                                    'background_polling': 10,
                                                                                    'transitional_states_polling': 2},
                                                                    'ssh':{'paramiko_host_key_policy_check': False},
                                                                    'stats':{'active': True,
                                                                            'max_queue_domains_status': 10,
                                                                            'max_queue_hyps_status': 10,
                                                                            'hyp_stats_interval': 5
                                                                            },
                                                                    'log':{
                                                                            'log_name':  'isard',
                                                                            'log_level': 'DEBUG',
                                                                            'log_file':  'msg.log'
                                                                    },
                                                                    'timeouts':{
                                                                            'ssh_paramiko_hyp_test_connection':   4,
                                                                            'timeout_trying_ssh': 2,
                                                                            'timeout_trying_hyp_and_ssh': 10,
                                                                            'timeout_queues': 2,
                                                                            'timeout_hypervisor': 10,
                                                                            'libvirt_hypervisor_timeout_connection': 3,
                                                                            'timeout_between_retries_hyp_is_alive': 1,
                                                                            'retries_hyp_is_alive': 3
                                                                            },
                                                                    'carbon':{'active':False,'server':'','port':''}},
                                                        'version':0,
                                                        'resources': {'code':False,
                                                                    'url':'http://www.isardvdi.com:5050'}
                                                       }], conflict='update').run())
                log.info("Table config populated with defaults.")
                return True
            else:
                return False

    '''
    DISPOSABLES
    '''

    def disposables(self):
        with app.app_context():
            if not r.table_list().contains('disposables').run():
                log.info("Table disposables not found, creating and populating defaults...")
                r.table_create('disposables', primary_key="id").run()
                self.result(r.table('disposables').insert([{'id': 'default',
                                                         'active': False,
                                                         'name': 'Default',
                                                         'description': 'Default disposable desktops',
                                                         'nets':[],
                                                         'disposables':[]  #{'id':'','name':'','description':''}
                                                         }]).run())
                
            return True                

    '''
    BACKUPS
    '''

    def backups(self):
        with app.app_context():
            if not r.table_list().contains('backups').run():
                log.info("Table backups not found, creating and populating defaults...")
                r.table_create('backups', primary_key="id").run()
            return True                

    '''
    USERS
    Updated in Domains for
    '''

    def users(self):
        with app.app_context():
            if not r.table_list().contains('users').run():
                log.info("Table users not found, creating...")
                r.table_create('users', primary_key="id").run()
                r.table('users').index_create("group").run()
                r.table('users').index_wait("group").run()

                if r.table('users').get('admin').run() is None:
                    usr = [{'id': 'admin',
                           'name': 'Administrator',
                           'kind': 'local',
                           'active': True,
                           'accessed': time.time(),
                           'username': 'admin',
                           'password': self.passwd,
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
                           },
                          {'id': 'disposable',
                           'name': 'Disposable',
                           'kind': 'local',
                           'active': False,
                           'accessed': time.time(),
                           'username': 'disposable',
                           'password': self.passwd,
                           'role': 'user',
                           'category': 'disposables',
                           'group': 'disposables',
                           'mail': '',
                           'quota': {'domains': {'desktops': 99,
                                                 'desktops_disk_max': 999999999,  # 1TB
                                                 'templates': 99,
                                                 'templates_disk_max': 999999999,
                                                 'running': 99,
                                                 'isos': 99,
                                                 'isos_disk_max': 999999999},
                                     'hardware': {'vcpus': 8,
                                                  'memory': 20000000}},  # 10GB
                           }
                           ]
                    self.result(r.table('users').insert(usr, conflict='update').run())
                    log.info("  Inserted default admin username with password isard")
                if r.table('users').get('eval').run() is None:
                    usr = [{'id': 'eval',
                            'name': 'Evaluator',
                            'kind': 'local',
                            'active': False,
                            'accessed': time.time(),
                            'username': 'eval',
                            'password': self.p.generate_human(8),
                            'role': 'admin',
                            'category': 'admin',
                            'group': 'eval',
                            'mail': 'eval@isard.io',
                            'quota': {'domains': {'desktops': 99,
                                                  'desktops_disk_max': 999999999,  # 1TB
                                                  'templates': 99,
                                                  'templates_disk_max': 999999999,
                                                  'running': 99,
                                                  'isos': 99,
                                                  'isos_disk_max': 999999999},
                                      'hardware': {'vcpus': 8,
                                                   'memory': 20000000}},  # 10GB
                            },
                           ]
                    self.result(r.table('users').insert(usr, conflict='update').run())
                    log.info("  Inserted default eval username with random password")
            return True

    '''
    VOUCHERS
    Grant access on new voucher
    '''

    def vouchers(self):
        with app.app_context():
            if not r.table_list().contains('vouchers').run():
                log.info("Table vouchers not found, creating...")
                r.table_create('vouchers', primary_key="id").run()
                #~ r.table('users').index_create("group").run()
                #~ r.table('users').index_wait("group").run()
            return True


    '''
    ROLES
    '''

    def roles(self):
        with app.app_context():
            if not r.table_list().contains('roles').run():
                log.info("Table roles not found, creating and populating...")
                r.table_create('roles', primary_key="id").run()
                self.result(r.table('roles').insert([{'id': 'user',
                                                      'name': 'User',
                                                      'description': 'Can create desktops and start it',
                                                      'quota': {'domains': {'desktops': 3,
                                                                            'desktops_disk_max': 60000000,
                                                                            'templates': 0,
                                                                            'templates_disk_max': 0,
                                                                            'running': 1,
                                                                            'isos': 0,
                                                                            'isos_disk_max': 0},
                                                                'hardware': {'vcpus': 2,
                                                                             'memory': 2500000}},  # 2,5GB
                                                      },
                                                     {'id': 'advanced',
                                                      'name': 'Advanced user',
                                                      'description': 'Can create desktops and templates and start desktops',
                                                      'quota': {'domains': {'desktops': 6,
                                                                            'desktops_disk_max': 90000000,
                                                                            'templates': 4,
                                                                            'templates_disk_max': 50000000,
                                                                            'running': 2,
                                                                            'isos': 3,
                                                                            'isos_disk_max': 3000000},
                                                                'hardware': {'vcpus': 3,
                                                                             'memory': 3000000}},  # 3GB
                                                      },
                                                     {'id': 'admin',
                                                      'name': 'Administrator',
                                                      'description': 'Is God',
                                                      'quota': {'domains': {'desktops': 12,
                                                                            'desktops_disk_max': 150000000,
                                                                            'templates': 8,
                                                                            'templates_disk_max': 150000000,
                                                                            'running': 4,
                                                                            'isos': 6,
                                                                            'isos_disk_max': 8000000},
                                                                'hardware': {'vcpus': 4,
                                                                             'memory': 4000000}}  # 10GB
                                                      }]).run())
            return True

    '''
    CATEGORIES
    '''

    def categories(self):
        with app.app_context():
            if not r.table_list().contains('categories').run():
                log.info("Table categories not found, creating...")
                r.table_create('categories', primary_key="id").run()

                if r.table('categories').get('admin').run() is None:
                    self.result(r.table('categories').insert([{'id': 'admin',
                                                               'name': 'Admin',
                                                               'description': 'Administrator',
                                                               'quota': r.table('roles').get('admin').run()[
                                                                   'quota']
                                                               }]).run())
                if r.table('categories').get('local').run() is None:
                    self.result(r.table('categories').insert([{'id': 'local',
                                                               'name': 'Local',
                                                               'description': 'Local users',
                                                               'quota': r.table('roles').get('user').run()[
                                                                   'quota']
                                                               }]).run())
                if r.table('categories').get('disposables').run() is None:
                    self.result(r.table('categories').insert([{'id': 'disposables',
                                                               'name': 'disposables',
                                                               'description': 'Disposable desktops',
                                                               'quota': r.table('roles').get('user').run()[
                                                                   'quota']
                                                               }]).run())
            return True

    '''
    GROUPS
    '''

    def groups(self):
        with app.app_context():
            if not r.table_list().contains('groups').run():
                log.info("Table groups not found, creating...")
                r.table_create('groups', primary_key="id").run()

                if r.table('groups').get('admin').run() is None:
                    self.result(r.table('groups').insert([{'id': 'admin',
                                                           'name': 'admin',
                                                           'description': 'Administrator',
                                                           'quota': r.table('roles').get('admin').run()['quota']
                                                           }]).run())
                if r.table('groups').get('users').run() is None:
                    self.result(r.table('groups').insert([{'id': 'local',
                                                           'name': 'local',
                                                           'description': 'Local users',
                                                           'quota': r.table('roles').get('user').run()['quota']
                                                           }]).run())

                if r.table('groups').get('advanced').run() is None:
                    self.result(r.table('groups').insert([{'id': 'advanced',
                                                           'name': 'Advanced',
                                                           'description': 'Advanced users',
                                                           'quota': r.table('roles').get('advanced').run()[
                                                               'quota']
                                                           }]).run())
                if r.table('groups').get('disposables').run() is None:
                    self.result(r.table('groups').insert([{'id': 'disposables',
                                                           'name': 'disposables',
                                                           'description': 'Disposable desktops',
                                                           'quota': r.table('roles').get('user').run()[
                                                               'quota']
                                                           }]).run())
            if r.table('groups').get('eval').run() is None:
                self.result(r.table('groups').insert([{'id': 'eval',
                                                       'name': 'eval',
                                                       'description': 'Evaluator',
                                                       'quota': r.table('roles').get('admin').run()['quota']
                                                       }]).run())
        return True

    '''
    INTERFACE
    '''

    def interfaces(self):
        with app.app_context():
            if not r.table_list().contains('interfaces').run():
                log.info("Table interfaces not found, creating and populating default network...")
                r.table_create('interfaces', primary_key="id").run()
                r.table("interfaces").index_create("roles", multi=True).run()
                r.table("interfaces").index_wait("roles").run()
                r.table("interfaces").index_create("categories", multi=True).run()
                r.table("interfaces").index_wait("categories").run()
                r.table("interfaces").index_create("groups", multi=True).run()
                r.table("interfaces").index_wait("groups").run()
                r.table("interfaces").index_create("users", multi=True).run()
                r.table("interfaces").index_wait("users").run()
                self.result(r.table('interfaces').insert([{'id': 'default',
                                                           'name': 'Default',
                                                           'description': 'Default network',
                                                           'ifname': 'default',
                                                           'kind': 'network',
                                                           'model': 'virtio',
                                                           'net': '',
                                                           'allowed': {
                                                               'roles': [],
                                                               'categories': [],
                                                               'groups': [],
                                                               'users': []}
                                                           }]).run())
            return True

    '''
    GRAPHICS
    '''

    def graphics(self):
        with app.app_context():
            if not r.table_list().contains('graphics').run():
                log.info("Table graphics not found, creating and populating default network...")
                r.table_create('graphics', primary_key="id").run()
                self.result(r.table('graphics').insert([{'id': 'default',
                                                         'name': 'Default',
                                                         'description': 'Spice viewer',
                                                         'type':'spice',
                                                         'allowed': {
                                                             'roles': [],
                                                             'categories': [],
                                                             'groups': [],
                                                             'users': []},
                                                         },
                                                        {'id': 'vnc',
                                                         'name': 'VNC',
                                                         'description': 'Not functional',
                                                         'type':'vnc',
                                                         'allowed': {
                                                             'roles': ['admin'],
                                                             'categories': False,
                                                             'groups': False,
                                                             'users': False}
                                                         }]).run())
            return True

    '''
    VIDEOS
    '''

    def videos(self):
        with app.app_context():
            if not r.table_list().contains('videos').run():
                log.info("Table videos not found, creating and populating default network...")
                r.table_create('videos', primary_key="id").run()
                self.result(r.table('videos').insert([{'id': 'qxl32',
                                                       'name': 'QXL 32MB',
                                                       'description': 'QXL 32MB',
                                                       'ram': 32768,
                                                       'vram': 32768,
                                                       'model': 'qxl',
                                                       'heads': 1,
                                                       'allowed': {
                                                           'roles': ['admin'],
                                                           'categories': False,
                                                           'groups': False,
                                                           'users': False},
                                                       },
                                                       {'id': 'default',
                                                       'name': 'Default',
                                                       'description': 'Default video card',
                                                       'ram': 65536,
                                                       'vram': 65536,
                                                       'model': 'qxl',
                                                       'heads': 1,
                                                       'allowed': {
                                                           'roles': [],
                                                           'categories': [],
                                                           'groups': [],
                                                           'users': []},
                                                       },
                                                      {'id': 'vga',
                                                       'name': 'VGA',
                                                       'description': 'For old OSs',
                                                       'ram': 16384,
                                                       'vram': 16384,
                                                       'model': 'vga',
                                                       'heads': 1,
                                                       'allowed': {
                                                           'roles': ['admin'],
                                                           'categories': False,
                                                           'groups': False,
                                                           'users': False}
                                                       }
                                                       ]).run())
            return True

    '''
    BOOTS
    '''

    def boots(self):
        with app.app_context():
            if not r.table_list().contains('boots').run():
                log.info("Table boots not found, creating and populating default network...")
                r.table_create('boots', primary_key="id").run()
                self.result(r.table('boots').insert([{'id': 'disk',
                                                      'name': 'Hard Disk',
                                                      'description': 'Boot based on hard disk list order',
                                                      'allowed': {
                                                          'roles': [],
                                                          'categories': [],
                                                          'groups': [],
                                                          'users': []}},
                                                     {'id': 'iso',
                                                      'name': 'CD/DVD',
                                                      'description': 'Boot based from ISO',
                                                      'allowed': {
                                                          'roles': ['admin'],
                                                          'categories': False,
                                                          'groups': False,
                                                          'users': False}},
                                                     {'id': 'pxe',
                                                      'name': 'PXE',
                                                      'description': 'Boot from network',
                                                      'allowed': {
                                                          'roles': ['admin'],
                                                          'categories': False,
                                                          'groups': False,
                                                          'users': False}}
                                                     ]).run())
            return True

    '''
    DISKS
    '''

    def disks(self):
        with app.app_context():
            if not r.table_list().contains('disks').run():
                log.info("Table disks not found, creating and populating default disk...")
                r.table_create('disks', primary_key="id").run()
                self.result(r.table('disks').insert([{'id': 'default',
                                                      'name': 'Default',
                                                      'description': 'Default',
                                                      "bus": "virtio",
                                                      "dev": "vda",
                                                      "type": "qcow2",
                                                      'allowed': {
                                                          'roles': [],
                                                          'categories': [],
                                                          'groups': [],
                                                          'users': []}}
                                                     ]).run())
            return True

    '''
    ISOS and FLOPPY:
    '''

    def media(self):
        with app.app_context():
            if not r.table_list().contains('media').run():
                log.info("Table media not found, creating...")
                r.table_create('media', primary_key="id").run()
                r.table('media').index_create("status").run()
                r.table('media').index_wait("status").run()
                r.table('media').index_create("user").run()
                r.table('media').index_wait("user").run()
        return True

    '''
    HYPERVISORS
    '''

    def hypervisors(self):
        '''
        Read RethinkDB configuration from file
        '''
        import configparser
        import os
        if os.path.isfile(os.path.join(os.path.join(os.path.dirname(__file__),'../../isard.conf'))):
            try:
                rcfg = configparser.ConfigParser()
                rcfg.read(os.path.join(os.path.dirname(__file__),'../../isard.conf'))
            except Exception as e:
                log.info('isard.conf file can not be opened. \n Exception: {}'.format(e))
                sys.exit(0)
        
        with app.app_context():
            if not r.table_list().contains('hypervisors').run():
                log.info("Table hypervisors not found, creating and populating with localhost")
                r.table_create('hypervisors', primary_key="id").run()

                rhypers = r.table('hypervisors')
                log.info("Table hypervisors found, populating...")
                if rhypers.count().run() == 0:
                    for key,val in dict(rcfg.items('DEFAULT_HYPERVISORS')).items():
                        vals=val.split(',')
                        self.result(rhypers.insert([{'id': key,
                                                     'hostname': vals[0],
                                                     'viewer_hostname': self._hypervisor_viewer_hostname(vals[1]),
                                                     'user': vals[2],
                                                     'port': vals[3],
                                                     'uri': '',
                                                     'capabilities': {'disk_operations': True if int(vals[4]) else False,
                                                                      'hypervisor': True if int(vals[5]) else False},
                                                     'hypervisors_pools': [vals[6]],
                                                     'enabled': True if int(vals[7]) else False,
                                                     'status': 'Offline',
                                                     'status_time': False,
                                                     'prev_status': [],
                                                     'detail': '',
                                                     'description': 'Default hypervisor',
                                                     'info': []},
                                                    ]).run())  
                    self.hypervisors_pools(disk_operations=[key])
        return True

    '''
    HYPERVISORS POOLS
    '''

    def hypervisors_pools(self,disk_operations=['localhost']):
        with app.app_context():
            if not r.table_list().contains('hypervisors_pools').run():
                log.info("Table hypervisors_pools not found, creating...")
                r.table_create('hypervisors_pools', primary_key="id").run()

                rpools = r.table('hypervisors_pools')

                self.result(rpools.delete().run())
                log.info("Table hypervisors_pools found, populating...")
                self.result(rpools.insert([{'id': 'default',
                                            'name': 'Default',
                                            'description': 'Non encrypted (not recommended)',
                                            'paths': {'bases':
                                                          [{'path':'/isard/bases',
                                                               'disk_operations': disk_operations, 'weight': 100}],
                                                      'groups':
                                                          [{'path':'/isard/groups',
                                                               'disk_operations': disk_operations, 'weight': 100}],
                                                      'templates':
                                                          [{'path':'/isard/templates',
                                                               'disk_operations': disk_operations, 'weight': 100}],
                                                      'disposables':
                                                          [{'path':'/isard/disposables',
                                                               'disk_operations': disk_operations, 'weight': 100}],
                                                      'isos':
                                                          [{'path':'/isard/isos',
                                                               'disk_operations': disk_operations, 'weight': 100}],
                                                      },
                                            'viewer':self._secure_viewer(),
                                            'interfaces': [],
                                            'allowed': {
                                                          'roles': [],
                                                          'categories': [],
                                                          'groups': [],
                                                          'users': []}
                                            }], conflict='update').run())
            return True

    '''
    HYPERVISORS_EVENTS
    '''

    def hypervisors_events(self):
        with app.app_context():
            if not r.table_list().contains('hypervisors_events').run():
                log.info("Table hypervisors_events not found, creating...")
                r.table_create('hypervisors_events', primary_key="id").run()
                r.table('hypervisors_events').index_create("domain").run()
                r.table('hypervisors_events').index_wait("domain").run()
                r.table('hypervisors_events').index_create("event").run()
                r.table('hypervisors_events').index_wait("event").run()
                r.table('hypervisors_events').index_create("hyp_id").run()
                r.table('hypervisors_events').index_wait("hyp_id").run()
            return True

    '''
    HYPERVISORS_STATUS
    '''

    def hypervisors_status(self):
        with app.app_context():
            if not r.table_list().contains('hypervisors_status').run():
                log.info("Table hypervisors_status not found, creating...")
                r.table_create('hypervisors_status', primary_key="id").run()
                r.table('hypervisors_status').index_create("connected").run()
                r.table('hypervisors_status').index_wait("connected").run()
                r.table('hypervisors_status').index_create("hyp_id").run()
                r.table('hypervisors_status').index_wait("hyp_id").run()
            if not r.table_list().contains('hypervisors_status_history').run():
                log.info("Table hypervisors_status_history not found, creating...")
                r.table_create('hypervisors_status_history', primary_key="id").run()
                r.table('hypervisors_status_history').index_create("connected").run()
                r.table('hypervisors_status_history').index_wait("connected").run()
                r.table('hypervisors_status_history').index_create("hyp_id").run()
                r.table('hypervisors_status_history').index_wait("hyp_id").run()
            return True

    '''
    DOMAINS
    '''

    def domains(self):
        with app.app_context():
            if not r.table_list().contains('domains').run():
                log.info("Table domains not found, creating...")
                r.table_create('domains', primary_key="id").run()
                r.table('domains').index_create("status").run()
                r.table('domains').index_wait("status").run()
                r.table('domains').index_create("hyp_started").run()
                r.table('domains').index_wait("hyp_started").run()
                r.table('domains').index_create("user").run()
                r.table('domains').index_wait("user").run()
                r.table('domains').index_create("group").run()
                r.table('domains').index_wait("group").run()
                r.table('domains').index_create("category").run()
                r.table('domains').index_wait("category").run()
                r.table('domains').index_create("kind").run()
                r.table('domains').index_wait("kind").run()
            return True
            
    '''
    DOMAINS_STATUS
    '''

    def domains_status(self):
        with app.app_context():
            if not r.table_list().contains('domains_status').run():
                log.info("Table domains_status not found, creating...")
                r.table_create('domains_status', primary_key="id").run()
                r.table('domains_status').index_create("name").run()
                r.table('domains_status').index_wait("name").run()
                r.table('domains_status').index_create("hyp_id").run()
                r.table('domains_status').index_wait("hyp_id").run()
            if not r.table_list().contains('domains_status_history').run():
                log.info("Table domains_status_history not found, creating...")
                r.table_create('domains_status_history', primary_key="id").run()
                r.table('domains_status_history').index_create("name").run()
                r.table('domains_status_history').index_wait("name").run()
                r.table('domains_status_history').index_create("hyp_id").run()
                r.table('domains_status_history').index_wait("hyp_id").run()
            return True
            
    '''
    DISK_OPERATIONS
    '''

    def disk_operations(self):
        with app.app_context():
            if not r.table_list().contains('disk_operations').run():
                log.info("Table disk_operations not found, creating...")
                r.table_create('disk_operations', primary_key="id").run()
            return True

    '''
    HELPERS
    '''
    
    def result(self, res):
        if res['errors']:
            log.error(res['first_error'])
            exit(0)

    def _parseString(self, txt):
        import re, unicodedata, locale
        if type(txt) is not str:
            txt = txt.decode('utf-8')
        locale.setlocale(locale.LC_ALL, 'ca_ES')
        prog = re.compile("[-_àèìòùáéíóúñçÀÈÌÒÙÁÉÍÓÚÑÇ .a-zA-Z0-9]+$", re.L)
        if not prog.match(txt):
            return False
        else:
            # ~ Replace accents
            txt = ''.join((c for c in unicodedata.normalize('NFD', txt) if unicodedata.category(c) != 'Mn'))
            return txt.replace(" ", "_")

    def _secure_viewer(self):
        cert_file='install/viewer-certs/ca-cert.pem'
        cert_file=''
        try:
            with open(cert_file, "r") as caFile:
                ca=caFile.read()
            from OpenSSL import crypto
            cert = crypto.load_certificate(crypto.FILETYPE_PEM, open(cert_file).read())
            return {'defaultMode':'Secure',
                                'certificate':ca,
                                'domain':cert.get_issuer().organizationName}
        except Exception as e:
            log.warning('Using insecure viewer. Non ssl encrypted!')
            return {'defaultMode':'Insecure',
                                'certificate':'',
                                'domain':''}

    def _hypervisor_viewer_hostname(self,viewer_hostname):
        hostname_file='install/host_name'
        try:
            with open(hostname_file, "r") as hostFile:
                return hostFile.read().strip()
        except Exception as e:
            return viewer_hostname

        return 
        
    '''
    LOCATIONS
    '''

    def hosts_viewers(self):
        with app.app_context():
            if not r.table_list().contains('hosts_viewers').run():
                log.info("Table hosts_viewers not found, creating...")
                r.table_create('hosts_viewers', primary_key="id").run()
                r.table('hosts_viewers').index_create("hostname").run()
                r.table('hosts_viewers').index_wait("hostname").run()
                r.table('hosts_viewers').index_create("mac").run()
                r.table('hosts_viewers').index_wait("mac").run()
                r.table('hosts_viewers').index_create("place_id").run()
                r.table('hosts_viewers').index_wait("place_id").run()
            return True
            
    '''
    PLACES
    '''

    def places(self):
        with app.app_context():
            if not r.table_list().contains('places').run():
                log.info("Table places not found, creating...")
                r.table_create('places', primary_key="id").run()
                r.table('places').index_create("network").run()
                r.table('places').index_wait("network").run()
                r.table('places').index_create("status").run()
                r.table('places').index_wait("status").run()
            return True


    '''
    BUILDER
    '''

    def builders(self):
        with app.app_context():
            if not r.table_list().contains('builders').run():
                log.info("Table builders not found, creating...")
                r.table_create('builders', primary_key="id").run()
            return True


    '''
    VIRT BUILDER
    '''

    def virt_builder(self):
        with app.app_context():
            if not r.table_list().contains('virt_builder').run():
                log.info("Table virt_builder not found, creating...")
                r.table_create('virt_builder', primary_key="id").run()
            return True

    '''
    VIRT INSTALL
    '''

    def virt_install(self):
        with app.app_context():
            if not r.table_list().contains('virt_install').run():
                log.info("Table virt_install not found, creating...")
                r.table_create('virt_install', primary_key="id").run()
            return True
