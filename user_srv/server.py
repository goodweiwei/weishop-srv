import argparse
import logging
import os
import signal
import socket
import sys
from concurrent import futures
from functools import partial

import grpc
from loguru import logger

from common.grpc_health.v1 import health_pb2_grpc, health
from common.register import consul
from user_srv.settings import settings

BASE_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, BASE_DIR)

from user_srv.handler.user import UserServicer
from user_srv.proto import user_pb2_grpc


def get_free_tcp_port():
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.bind(("", 0))
    _, port = tcp.getsockname()
    tcp.close()
    return port


def on_exit(signo, frame, service_id):
    register = consul.ConsulRegister(settings.CONSUL_HOST, settings.CONSUL_PORT)
    logger.info(f"注销 {service_id} 服务")
    register.deregister(service_id)
    logger.info("注销成功")
    sys.exit(0)


def run_service():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip",
                        nargs="?",
                        type=str,
                        default="82.157.166.247",
                        help="binding ip"
                        )
    parser.add_argument("--port",
                        nargs="?",
                        type=int,
                        default=50051,
                        help="the listening port"
                        )
    args = parser.parse_args()
    print(args.port, args.ip)
    if args.port == 0:
        port = get_free_tcp_port()
    else:
        port = args.port

    logger.add("logs/user_srv_{time}.log")

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # 注册用户服务
    user_pb2_grpc.add_UserServicer_to_server(UserServicer(), server=server)

    #注册健康检查
    health_pb2_grpc.add_HealthServicer_to_server(health.HealthServicer(), server)

    server.add_insecure_port(f"[::]:{args.port}")

    import uuid
    service_id = str(uuid.uuid1())

    # 主进程退出信号监听
    """
        windows下支持的信号是有限的：
            SIGINT ctrl+C终端
            SIGTERM kill发出的软件终止
    """
    signal.signal(signal.SIGINT, partial(on_exit, service_id=service_id))
    signal.signal(signal.SIGTERM, partial(on_exit, service_id=service_id))

    logger.info(f"服务启动：{args.ip}:{args.port}")
    server.start()

    logger.info("服务注册开始")
    register = consul.ConsulRegister(settings.CONSUL_HOST, settings.CONSUL_PORT)
    if not register.register(name=settings.SERVICE_NAME, id=service_id,
                             address=args.ip, port=port, tags=settings.SERVICE_TAGS, check=None):
        logging.info("服务注册失败")
        sys.exit(0)

    logger.info("服务启动成功")
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig()
    run_service()
