import configparser
import os.path

config = configparser.ConfigParser()
file_dir = os.path.dirname(__file__)
config.read(file_dir + '\\db.config')
