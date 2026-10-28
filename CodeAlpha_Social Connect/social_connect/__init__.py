import pymysql

pymysql.install_as_MySQLdb()

# Compatibility with MariaDB / MySQL versions across various environments
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.mysql.features import DatabaseFeatures

BaseDatabaseWrapper.check_database_version_supported = lambda self: None

def _can_return_columns_from_insert(self):
    return self.connection.mysql_is_mariadb and self.connection.mysql_version >= (10, 5, 0)

DatabaseFeatures.can_return_columns_from_insert = property(_can_return_columns_from_insert)
