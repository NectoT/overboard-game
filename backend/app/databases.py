'''Простой модуль для хранения и инициализации подключений к базам данных'''

import pymongo
from pymongo.database import Database

# Ну я подразумеваю, что во время исполнения программы не нужно будет переподключаться по
# другому url

MONGO_DATABASE_URL = 'localhost'

mongo_client = pymongo.MongoClient(MONGO_DATABASE_URL)
mongo_db: Database = mongo_client['overboard']