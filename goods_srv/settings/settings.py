import json

import nacos
from loguru import logger
from playhouse.pool import PooledMySQLDatabase
from playhouse.shortcuts import ReconnectMixin


# 使用peewee连接池，使用ReconnectMixin来防止出现连接断开查询失败
class ReconnectMysqlDatabase(ReconnectMixin, PooledMySQLDatabase):
    pass


NACOS = {
    "Host": "82.157.166.247",
    "Port": 8848,
    "NameSpace": "05ef56f1-cf3c-4bcd-bbfc-86bdd9cc3fac",
    "User": "nacos",
    "Password": "nacos",
    "DataId": "goods-srv",
    "Group": "dev"
}

client = nacos.NacosClient(server_addresses=f"{NACOS['Host']}:{NACOS['Port']}",
                           username=NACOS['User'], password=NACOS['Password'], namespace=NACOS["NameSpace"])

# get config
data = client.get_config(data_id=NACOS['DataId'], group=NACOS['Group'])
data = json.loads(data)
logger.info(data)


def update_cfg(args):
    print("配置产生变化")
    print(args)


# consul相关配置
CONSUL_HOST = data["consul"]["host"]
CONSUL_PORT = data["consul"]["port"]

# 服务相关配置
SERVICE_NAME = data["name"]
SERVICE_TAGS = data["tags"]

DB = ReconnectMysqlDatabase(data["mysql"]["db"], host=data["mysql"]["host"], port=data["mysql"]["port"],
                            user=data["mysql"]["user"], password=data["mysql"]["password"])
