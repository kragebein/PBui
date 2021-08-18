#!/usr/bin/python3.6
from flask import Flask, render_template, request, flash, redirect, abort, url_for
from src import config
from flask_cors import CORS
import requests
import sqlite3
import json
import youtube_dl
from pyyoutube import Api
from src.youtube import YoutubeSearch
from src.em import EmbyApi
import re
import subprocess
import hashlib
import random
import string
app = Flask(__name__)
CORS(app)
conf = config.Conf()
# login

class web():
    def __init__(self):
        conf.rest
        self.key = conf.rest
       
        self.api = 'https://plex.lazywack.no/rest/'
        self.endpoints = ['search', 'missing', 'request', 'imdb', 'refresh']
        # store temporary values here
        self.youtube_result = None
        self.youtube_trailers = {}
        self.signups = []
        self.allowedclients = [
            'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1',
            'GoNativeAndroid/1.0'] # GoNative Android Application.
            
    def create_user(self):
        ''' Set up a user creation system '''
        result_str = []
        result_str = ''.join(random.choice(string.ascii_letters) for i in range(10))
        result = hashlib.md5(result_str.encode())
        result = result.hexdigest()
        self.signups.append(result)
        print(self.signups)

        return result
        

    def index(self):
        data = EmbyApi()
        return render_template('announce.html', json=data.lastAdded())

    def get_lines(self, where):
        if where == 'project':
            x = subprocess.check_output('sh /home/krage/web/src/proj.sh', shell=True)
            return x.decode('ascii').strip()
        elif where == 'api':
            x = subprocess.check_output('sh /home/krage/web/src/api.sh', shell=True)
            return x.decode('ascii').strip()

    def search(self, title=None, results=None):
        if results == None and title == None:
            # No searches, no results, we'll return a blank page.
            return render_template('search.html')
        # Shouldnt get here
        return "ERROR"

    def episode(self, imdbid, season, episode, key):
        ''' returns episode data to jinja '''
        return json.loads(requests.get(self.api + self.key + '/imdb/' + '{}/{}/{}'.format(imdbid, season, episode)).text)

    def imdb(self, imdbid):
        ''' returns imdb item data to jinja '''
        return json.loads(requests.get(self.api + self.key + '/imdb/' + '{}'.format(imdbid)).text)

    def get_trailer(self):
        return 'iojhqm0JTW4'

    def get_youtube_trailer(self, _title, year, imdbid):
        if imdbid in self.youtube_trailers:
            return self.youtube_trailers[imdbid]
        self.youtube_trailers[imdbid] = None
        return self.youtube_trailers[imdbid]
        if year == 'N/A':
            year = ''
        else:
            year = year.split(' ')
        results = YoutubeSearch(_title + year[2] if year != '' else '' +  'Trailer', max_results=10).to_dict()
        points = {}
        for i in results:
            id = i['id']
            points[id] = 0
            title = i['title']
            if _title.lower() in title.lower():
                points[id] += 1
            if 'movie' in title.lower() or 'series' in title.lower():
                points[id] += 1
            if 'trailer' in title.lower():
                points[id] += 1
            if year != '':
                match = re.match(r'.*([1-3][0-9]{3})', title)
                if match is not None:
                    # Then it found a match!
                    try:
                        if match.group(1) == year[2]:
                            points[id] += 3
                    except:
                        try:
                            if match.group(1) == year:
                                points[id] += 3
                        except:
                            pass
                        pass
            if 'official' in title.lower() and 'teaser' not in title.lower():
                points[id] += 2
            if 'teaser' in title.lower() and 'official' not in title.lower():
                points[id] += 1
            if 'hd' in title.lower():
                points[id] += 1
            if 'parody' in title.lower():
                points[id] -= 1
            if 'remix' in title.lower():
                points[id] -= 1
            if 'fanmade' in title.lower():
                points[id] -= 1
            if 'review' in title.lower():
                points[id] -= 3
            
            #print('trailer with name "{}" got {} points'.format(title, points[id]))
        data = {k: v for k, v in sorted(points.items(), key=lambda item: item[1])}
        try:
            self.youtube_trailers[imdbid] = str(list(data)[-1])
        except:
            self.youtube_trailers[imdbid] = None
        return self.youtube_trailers[imdbid]
        
    def blist(self, _list):
        data = []
        for i in _list:
            data.append(json.loads(requests.get(self.api + self.key + '/imdb/' + i).text))
        return data


    def crash(self):
        return False
    
    def request_(self, imdbid):
        req = request.req(self.api + self.key + '/request/' + imdbid).text
        return req

    def _requests(self):
        ''' Request the active requests from rest API '''
        r = requests.get(self.api + self.key + '/activerequets')
        if r.status_code == 200:
            return r.text
        else:
            return False

    def checkbrowser(self, browser):
        for agent in self.allowedclients:
            if agent in browser:
                return True

        print(f'^^ is disallowed because of agent.')
        return False

x = web()
e = EmbyApi()
@app.context_processor
def self_x():
    return dict(Web=x)
@app.route('/test')
def _test():
    return render_template('test.html')

@app.route('/requests')
def _requests():
    ''' Renter active requets from rest api template '''
    return render_template('requests.html', data=x._requests(), web=x)

@app.route('/id/<_id>', methods=('POST', 'GET'))
def ident(_id):
    ''' Checks wether or not this app is authorized and by whom. '''
    r = sqlite3.connect('users.db')
    sql = r.cursor()
    query = 'SELECT username FROM users WHERE id = "{}"'.format(_id)
    data = sql.execute(query).fetchone()
    if data == None:
        return render_template('signup.html', x=request, _id=_id)
    return f'registered {data[0]}' 
    
@app.route('/status')
def stats():
    if x.checkbrowser(request.headers.get('User-Agent')):
        stat = e.getSessions()
        return render_template('status.html', x=x, stat=stat)
    else:
        return render_template('disallowed.html')
@app.route('/')
def index():
    print('Route /: {}'.format(request.headers.get('User-Agent')))
    if x.checkbrowser(request.headers.get('User-Agent')):
        return x.index()
    else:
        return render_template('disallowed.html', x=request)

@app.route('/request', methods=('GET', 'POST'))
def _request():
    if x.checkbrowser(request.headers.get('User-Agent')):
        if request.method == 'POST':
            imdbid = request.form['imdb']
            data = json.loads(requests.get(x.api + x.key + '/request/' + imdbid).text)
            return render_template('request.html', results=data, imdb=json.loads(requests.get(x.api + x.key + '/imdb/' + imdbid).text))
        else:
            return render_template('index.html', x=x)
    else:
        return render_template('disallowed.html')

@app.route('/subtitles', methods=('GET', 'POST'))
def subtitle():
    if request.method == 'POST':
        result = json.loads(requests.get(x.api + x.key + '/emby/' + request.form['id']).text)
        print(result)
        length = result['TotalRecordCount']
        patharray = {}
        name = None
        for result in result['Items']:
            filename = result['Path'].split('/')[-1]
            path = result['Path'].replace(filename, '')
            patharray[path] = filename
            name = result['Name']
        return render_template('subtitle.html', x=result, length=length, p=patharray, name=name)
    else:

        return render_template('subtitle.html', x=None)

@app.route('/yt')
def yt():
    return x.youtube_trailers

@app.route('/search', methods=('GET', 'POST'))
def search():
    if x.checkbrowser(request.headers.get('User-Agent')):
        if request.method == 'POST':
            title = request.form['title']
            title = title.strip()
            if len(title) <= 1:
                return render_template('searchresults.html', querylen=True)
            data = requests.get(x.api + x.key + '/search/' + title)
            results = json.loads(data.text)
            if results['message'] == 'Unauthorized':
                render_template('500.html')
            try:
                # try to sort results by year.
                results = dict(sorted(results.items(), key=lambda i: i[1]['year'], reverse=True))
            except:
                pass
            imdbdata = x.blist([i for i in results])
            omitted = 0
            for i in imdbdata:
                try:
                    if i['result']['poster'] == 'N/A':
                        omitted += 1
                except:
                    pass
            match = len(imdbdata)
                
            return render_template('searchresults.html', results=results, data=imdbdata, matches=match, x=x, omitted=omitted, querylen=False)
        else:
            return x.search()
    else:
        return render_template('disallowed.html')
@app.route('/request/<imdbid>')
def test(imdbid):
    return render_template('test.html', data=imdbid)

@app.route('/projectstatus')
def projectstatus():
    return render_template('index.html', x=x)

@app.route('/agent')
def idid():
    return request.headers.get('User-Agent')

@app.route('/test/<imdbid>')
def reequest(imdbid):
    x = web()
    return render_template('test.html', data=imdbid)

@app.route('/announce')
def ann():
    return render_template('announce.html', json=None)

@app.route('/track')
def tracker():
    x = web()
    return render_template('tracker.html')

@app.route('/refresh', methods=('GET', 'POST'))
def refreshitem():
    if request.method == 'POST':
        if 'force' in request.form:
            print('Forcing a new request for an already existing object.')
            return render_template('refreshitem.html', item = request.method['force'])
    else:
        return render_template('disallowed.html')
        
@app.route('/adminer', methods=('GET', 'POST'))
def adminer():
    if request.method == 'GET':
        return render_template('adminer.html', x=None)
    elif request.method == 'POST':
        if request.form['create'] == 'create':
            return render_template('adminer.html', x=x.create_user())
    else:
        return render_template('adminer.html', x=None)
        
@app.route('/signup', methods=('GET', 'POST'))
def signup():
    _id = ''
    if request.method == 'POST':
        username = request.form['username']
        _id = request.form['_id']
        users = e.getUsers()
        userlist = []
        for y in users:
            userlist.append(y['Name'])
        if username in userlist:
            # This user actually exists, lets add it to the database.
            r = sqlite3.connect('users.db')
            sql = r.cursor()
            query = 'SELECT id FROM users WHERE username = "{}"'.format(username)
            sql.execute(query).fetchall()
            # return user to signup if this user is already registered.
            if sql.execute(query).fetchone() is not None:
                return render_template('signup.html', _id=_id, invalid=True)
            query = "REPLACE into users VALUES(?,?)"
            sql.execute(query, [username, _id])
            r.commit()
            return x.index()
        else:
            return render_template('signup.html', _id=_id, invalid=True)
    return render_template('signup.html', _id=_id)

@app.errorhandler(404)
def page_not_found404(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404

@app.errorhandler(500)
def page_not_found500(e):
    # note that we set the 404 status explicitly
    return render_template('500.html'), 404


app.run(host='0.0.0.0', port='5555', debug=True)


