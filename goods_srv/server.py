import argparse
import logging
import os
import signal
import socket
import sys
import uuid
from concurrent import futures
from functools import partial

import grpc
from loguru import logger

from goods_srv.handler.goods import GoodsServicer

BASE_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, BASE_DIR)

from common.grpc_health.v1 import health_pb2_grpc, health
from common.register import consul
from goods_srv.proto import goods_pb2, goods_pb2_grpc
from goods_srv.settings import settings


def on_exit(service_id):
    register = consul.ConsulRegister(settings.CONSUL_HOST, settings.CONSUL_PORT)
    logger.info(f"注销 {service_id} 服务")
    register.deregister(service_id=service_id)
    logger.info("注销成功")
    sys.exit(0)


def get_free_tcp_port():
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.bind(("", 0))
    _, port = tcp.getsockname()
    tcp.close()
    return port


def run_service():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ip',
                        nargs="?",
                        type=str,
                        default='127.0.0.1',
                        help='binding ip'
                        )
    parser.add_argument("--port",
                        nargs="?",
                        type=str,
                        default=0,
                        help="the listening port"
                        )
    args = parser.parse_args()

    if args.port == 0:
        port = get_free_tcp_port()
    else:
        port = args.port

    logger.add("logs/goods_srv_{time}.log")

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # 注册商品服务
    goods_pb2_grpc.add_GoodsServicer_to_server(GoodsServicer(), server)

    # 注册健康检查
    health_pb2_grpc.add_HealthServicer_to_server(health.HealthServicer(), server)

    server.add_insecure_port(f"{args.ip}:{port}")

    service_id = str(uuid.uuid1())

    # 主进程退出信号监听
    signal.signal(signal.SIGINT, partial(on_exit, service_id=service_id))
    signal.signal(signal.SIGTERM, partial(on_exit, service_id=service_id))

    logger.info(f"启动服务：{args.ip}:{port}")
    server.start()

    logger.info("服务注册开始")
    register = consul.ConsulRegister(settings.CONSUL_HOST, settings.CONSUL_PORT)
    if not register.register(name=settings.SERVICE_NAME, id=service_id, address=args.ip, port=port,
                             tags=settings.SERVICE_TAGS, check=None):
        logger.info("服务注册失败")
        sys.exit(0)
    logger.info("服务注册成功")
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig()
    run_service()
