''' Configuration file '''
class Conf():
    def __init__(self):
        import configparser as cf
        config = cf.ConfigParser()
        config.read('config.ini')
        keys = config['keys']
        self.emby = keys['emby']
        self.rest = keys['rest']


