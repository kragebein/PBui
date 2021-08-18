#!/usr/bin/python3.6
''' Request tracker module '''
import sqlite3
import requests
import subprocess
import json
 

class Track():
    def __init__(self):
        ''' Set some global vars '''
        self.rtorrent = None
        self.cache = None
        self.array = None
        self.cloud = None
        self.plex = None
        self.track = None
        try: 
            self.db = sqlite3.connect('tracker.db')
            self.dbc = self.db.cursor()
            self.olddata = self.dbc.execute('SELECT * from tracker').fetchall()
            self.olddata = json.loads(self.olddata)
        except:
            self.dbc = None
            self.olddata = {}

    def track(self, id=None, num=5):
        ''' tracks a specific request, or list last 5 requests ''' 
        