import pymongo
from django.conf import settings
from datetime import datetime
import hashlib

class MongoDBConnection:
    def __init__(self):
        self.client = pymongo.MongoClient(
            settings.MONGODB_SETTINGS['host'], 
            settings.MONGODB_SETTINGS['port']
        )
        self._db = self.client[settings.MONGODB_SETTINGS['database']]
    
    def get_collection(self, collection_name):
        return self._db[collection_name]
    
    def insert_user(self, user_data):
        collection = self.get_collection('resume_login')
        return collection.insert_one(user_data)
    
    def find_user(self, query):
        collection = self.get_collection('resume_login')
        return collection.find_one(query)
    
    def authenticate_user(self, username, password):
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        user = self.find_user({
            'username': username,
            'password_hash': password_hash
        })
        return user