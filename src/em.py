#!/usr/bin/python3
import requests, json, logging, traceback
from src import config
conf = config.Conf()
class EmbyApi():
    ''' Class handling api to Emby '''
    def get(self, **kwargs):
        ''' Requests data from Emby, returns raw json data '''
        headers = {'X-Emby-Token': conf.emby , 'accept': 'application/json', 'User-Agent': 'Mozilla/5.0 (MSIE 10.0; Windows NT 6.1; Trident/5.0)'}
        path = 'http://plex.wack:8096/emby/'
        params = {}
        if 'url' not in kwargs['data']:
            return 'ERROR MALFORMED REQUEST, URL REQUIRED'
        route = kwargs['data']['url']
        if 'headers' in kwargs['data']:
            headers = kwargs['data']['headers']
        if 'params' in kwargs['data']:
            params = kwargs['data']['params']
        data = requests.get(path + route, headers=headers, params=params)
        try: 
            data = json.loads(data.text)
        except:
            data = data.text
        return data

    def post(self, **kwargs):
        ''' Posts data to Emby, returns raw json data '''
        headers = {'X-Emby-Token': conf.emby, 'accept': 'application/json', 'User-Agent': 'Mozilla/5.0 (MSIE 10.0; Windows NT 6.1; Trident/5.0)'}
        path = 'http://plex.wack:8096/emby/'
        params = {}
        if 'url' not in kwargs['data']:
            return 'ERROR MALFORMED REQUEST, URL REQUIRED'
        route = kwargs['data']['url']
        if 'headers' in kwargs['data']:
            headers = kwargs['data']['headers']
        if 'params' in kwargs['data']:
            params = kwargs['data']['params']
        data = requests.post(path + route, headers=headers, params=params)
        try: 
            data = json.loads(data.text)
        except:
            data = data.text
        return data

    def itemImage(self, id):
        '''Return url of item banner '''
        url = 'https://e.lazywack.no/emby/Items/{}/Images/Logo/?tag=api&quality=90&maxWidth=390'.format(id)
        if requests.get(url).status_code == 200:
            return url
        else:
            url = 'https://e.lazywack.no/emby/Items/{}/Images/Banner/?tag=api&quality=90&maxWidth=390'.format(id)
        if requests.get(url).status_code == 200:
            return url
        else:
            url = 'https://e.lazywack.no/emby/Items/{}/Images/Primary/?tag=api&quality=90&maxWidth=390'.format(id)
        if requests.get(url).status_code == 200:
            return url

    def onEmby(self, _id):
        ''' returns data if item exists on Emby, False otherwise '''
        params = {'url': 'Items', 'params': {'AnyProviderIdEquals' : 'imdb.' + _id, 'Recursive': True}}
        data = self.get(data=params)
        if data['TotalRecordCount'] == 0:
            return False
        else: 
            return data

    def lastAdded(self):
        ''' returns a list of the last 5 last items added that isnt isnt in the future.'''
        item = {}   # Return this when filled
        params =  {'Limit':'5', 'GroupItems': 'False'}
        data = {'url': 'Users/6b7dee8f870740a2b9fa6bba416e8c62/Items/Latest', 'params': params}
        data = self.get(data=data)
        for x in data:               
            prm = {'url': 'Users/6b7dee8f870740a2b9fa6bba416e8c62/Items/' + str(x['Id'])}
            _item = self.get(data=prm)
            thing = ['Episode', 'Movie']
            if _item['Type'] in thing:
                if _item['MediaSources'][0]['Type'] != 'Placeholder': # Ignore future episodes.
                    item[x['Id']] = {}
                    if _item['Type'] == 'Episode':
                        
                        item[x['Id']]['type'] = _item['Type']
                        string = _item['DateCreated']
                        date = string.split('T')[0]
                        time = string.split('T')[1].split('.')[0]
                        added = '{} {}'.format(date, time)
                        item[x['Id']]['added'] = added
                        item[x['Id']]['show'] = _item['SeriesName']
                        item[x['Id']]['name'] = _item['Name'] if 'Overview' in _item else _item['SeriesName']
                        item[x['Id']]['year'] = _item['ProductionYear'] if 'ProductionYear' in _item else 'N/A'
                        item[x['Id']]['season'] = _item['ParentIndexNumber'] if 'ParentIndexNumber' in _item else 'N/A'
                        item[x['Id']]['episode'] = _item['IndexNumber'] if 'IndexNumber' in _item else 'N/A'
                        item[x['Id']]['plot'] = _item['Overview'] if 'Overview' in _item else 'This episode doesnt yet have a plot'
                        if 'SeriesId' in _item:
                            item[x['Id']]['poster'] = self.itemImage(_item['SeriesId'])
                        else: 
                            item[x['Id']]['poster'] = None
                        #item[x['Id']]['poster'] = self.itemImage(_item['Id']) if 'Id' in _item else 'N/A'
                    elif _item['Type'] == 'Movie':
                        string = _item['DateCreated']
                        date = string.split('T')[0]
                        time = string.split('T')[1].split('.')[0]
                        added = '{} {}'.format(date, time)
                        item[x['Id']]['added'] = added
                        item[x['Id']]['type'] = _item['Type']
                        item[x['Id']]['name'] = _item['Name']
                        item[x['Id']]['year'] = _item['ProductionYear'] if 'ProductionYear' in _item else 'N/A'
                        item[x['Id']]['plot'] = _item['Overview'] if 'Overview' in _item else 'This movie doesnt yet have a plot'
                        if 'ParentLogoItemId' in x:
                            item[x['Id']]['poster'] = self.itemImage(x['ParentLogoItemId'])
                        elif 'Id' in x:
                            item[x['Id']]['poster'] = self.itemImage(x['Id'])
                        else: 
                            item[x['Id']]['poster'] = None
        return item

    def refreshItem(self, id):
        ''' Refresh the metadata of this Item '''
        if not self.onEmby(id):
            return 'item does not exist on Emby'
        pass
        
    def getSubtitles(self, id):
        ''' Download subtitiles for this item '''
        data = self.onEmby(id)
        if not data:
            return 'item does not exist on Emby'
        params = {'url': 'Items/{}/RemoteSearch/Subtitles/ENG'.format(data['Items'][0]['Id']) }
        data = self.get(data=params)
        print(data)


    def getSessions(self):
        ''' returns sessions currently playing '''
        data = {'url': 'Sessions'}
        data = self.get(data=data)
        ret = {}
        cnt = 0
        for x in data:
            if 'NowPlayingItem' in x:
                ret[cnt] = {}   
                try:
                    ret[cnt]['id'] = data[cnt]['NowPlayingItem']['Id']
                    ret[cnt]['transcode'] = data[cnt]['PlayState']['PlayMethod']
                    print(data[cnt]['PlayState']['PlayMethod'])
                    ret[cnt]['state'] = 'paused' if data[cnt]['PlayState']['IsPaused'] == True else 'playing'
                    ret[cnt]['ticks'] = round(data[cnt]['PlayState']['PositionTicks'] / 10000000)
                    ret[cnt]['totalticks'] = round(data[cnt]['NowPlayingItem']['RunTimeTicks'] / 10000000)
                    ret[cnt]['length'] = round(data[cnt]['NowPlayingItem']['RunTimeTicks'] / 10000000 / 60)
                    ret[cnt]['progress'] = round((ret[cnt]['ticks'] / ret[cnt]['totalticks']) * 100)
                    ret[cnt]['user'] = data[cnt]['UserName']
                    ret[cnt]['client'] = data[cnt]['Client']
                    ret[cnt]['device'] = data[cnt]['DeviceName']
                    ret[cnt]['plot'] = data[cnt]['NowPlayingItem']['Overview'] if 'Overview' in data[cnt]['NowPlayingItem'] else 'N/A'
                    ret[cnt]['type'] = data[cnt]['NowPlayingItem']['Type']
                    if 'ParentLogoItemId' in data[cnt]['NowPlayingItem']:
                        ret[cnt]['poster'] = self.itemImage(data[cnt]['NowPlayingItem']['ParentLogoItemId'])
                    elif 'Id' in data[cnt]['NowPlayingItem']:
                        ret[cnt]['poster'] = self.itemImage(data[cnt]['NowPlayingItem']['Id'])
                    else:
                        ret[cnt]['poster'] = None
                    if ret[cnt]['type'] == 'Episode':
                        ret[cnt]['season'] = str(data[cnt]['NowPlayingItem']['ParentIndexNumber'])
                        ret[cnt]['episode'] = str(data[cnt]['NowPlayingItem']['IndexNumber'])
                        ret[cnt]['parent'] = data[cnt]['NowPlayingItem']['SeriesName']
                        ret[cnt]['child'] = data[cnt]['NowPlayingItem']['Name']
                        ret[cnt]['name'] = '{} - {}'.format(ret[cnt]['parent'],ret[cnt]['child'])
                    else:     
                        ret[cnt]['name'] = data[cnt]['NowPlayingItem']['Name']
                    for z in data[cnt]['NowPlayingItem']['MediaStreams']:
                        if z['Type'] == 'Video':
                            height = z['Height']
                            width = z['Width']
                            ret[cnt]['codec'] = z['DisplayTitle']
                            ret[cnt]['resolution'] = '{}x{}'.format(height, width)
                            ret[cnt]['bitrate'] = round(z['BitRate']  / 1024 / 1024,1)
                            ret[cnt]['hdr'] = True if z['VideoRange'] == 'HDR' else False
                except:
                    # print stack but continue.
                    traceback.print_exc()
                    del ret[cnt]
                    pass
            cnt += 1
        return ret
    def getUsers(self):
        ''' get list of users '''
        data = {'url': 'Users'}
        return self.get(data=data)

    def userPolicy(self, user, policy):
        if user is None or not isinstance(user, str):
            return 'got {} while expecting str'.format(type(user))
        if policy is None or not isinstance(policy, dict):
            return 'Failed. Missing policy or {} is not dict'.format(type(policy))
        data = {'url': 'Users/{}/Policy'.format(user), 'params': policy}
        return self.post(data=data)

    def getLibraryFolders(self):
        data = {'url': 'Library/MediaFolders'}
        return self.get(data=data)


