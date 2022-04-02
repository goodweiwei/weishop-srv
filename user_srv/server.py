import argparse
import logging
import os
import socket
import sys
from concurrent import futures

import grpc
from loguru import logger

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


def run_service():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip",
                        nargs="?",
                        type=str,
                        default="127.0.0.1",
                        help="binding ip"
                        )
    parser.add_argument("--port",
                        nargs="?",
                        type=int,
                        default=0,
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

    server.add_insecure_port(f"{args.ip}:{port}")

    # 启动服务
    server.start()
    logger.info("服务启动成功")
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig()
    run_service()
