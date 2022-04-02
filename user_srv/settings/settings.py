from playhouse.pool import PooledMySQLDatabase
from playhouse.shortcuts import ReconnectMixin


class ReconnectMysqlDatabase(ReconnectMixin, PooledMySQLDatabase):
    pass


# 数据库相关的配置
DATABASE = "mxshop_user"
DATABASE_HOST = "127.0.0.1"
DATABASE_PORT = 3306
DATABASE_USER = "root"
DATABASE_PASSWORD = "root"

DB = ReconnectMysqlDatabase(DATABASE, host=DATABASE_HOST, port=DATABASE_PORT, user=DATABASE_USER,
                            password=DATABASE_PASSWORD)
