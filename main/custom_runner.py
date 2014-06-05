from django.test.runner import DiscoverRunner
from django.conf import settings
from pymongo import MongoClient

# Check if database will use already defined test_database in settings_test.py
# or if is need change name in runtime
MONGO_DATABASE_NAME = settings.MONGO_DATABASE_NAME

if not MONGO_DATABASE_NAME.startswith('test_'):
    MONGO_DATABASE_NAME = 'test_%s' % MONGO_DATABASE_NAME


class TestRunner(DiscoverRunner):

    def setup_databases(self, **kwargs):
        db_name = MONGO_DATABASE_NAME
        conn = MongoClient()
        database = conn[db_name]
        print 'Creating test-database: ' + db_name

        return db_name

    def teardown_databases(self, old_config, **kwargs):
        from pymongo import MongoClient
        conn = MongoClient()
        db_name = old_config
        conn.drop_database(db_name)
        print 'Dropping test-database: ' + db_name
