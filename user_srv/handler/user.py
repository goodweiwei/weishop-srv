import time
from datetime import date

import grpc
from google.protobuf import empty_pb2
from loguru import logger
from passlib.handlers.pbkdf2 import pbkdf2_sha256
from peewee import DoesNotExist

from user_srv.model.models import User
from user_srv.proto import user_pb2, user_pb2_grpc


class UserServicer(user_pb2_grpc.UserServicer):
    def convert_user_to_rsp(self, user):
        # 将user的model对象转换成message对象
        user_info_rsp = user_pb2.UserInfoResponse()
        user_info_rsp.id = user.id
        user_info_rsp.password = user.password
        user_info_rsp.mobile = user.mobile
        user_info_rsp.role = user.role

        if user.nick_name:
            user_info_rsp.nickName = user.nick_name
        if user.gender:
            user_info_rsp.gender = user.gender
        if user.birthday:
            user_info_rsp.birthday = int(time.mktime(user.birthday.timetuple()))
        return user_info_rsp

    @logger.catch()
    def GetUserList(self, request, context):
        # 获取用户列表
        rsp = user_pb2.UserListResponse()
        users = User.select()
        rsp.total = users.count()
        start = 0
        per_page_nums = 10
        if request.pSize:
            per_page_nums = request.pSize
        if request.pn:
            start = per_page_nums * (request.pn - 1)
        users = users.limit(per_page_nums).offset(start)

        for user in users:
            rsp.data.append(self.convert_user_to_rsp(user))
        return rsp

    @logger.catch()
    def GetUserById(self, request, context):
        # 通过id查询用户
        try:
            user = User.get(User.id == request.id)
            print(user)
            return self.convert_user_to_rsp(user)
        except DoesNotExist as e:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("用户不存在")
            return user_pb2.UserInfoResponse()

    @logger.catch()
    def GetUserByMobile(self, request, context):
        # 通过手机号查询用户
        try:
            print(request.mobile)
            user = User.get(User.mobile == request.mobile)
            return self.convert_user_to_rsp(user)
        except DoesNotExist as e:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("用户不存在")
            return user_pb2.UserInfoResponse()

    @logger.catch()
    def CreatUser(self, request, context):
        # 新建用户，表单验证由gin验证，这里没有必要进行表单验证
        try:
            User.get(User.mobile == request.mobile)
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            context.set_details("用户已存在")
            return user_pb2.UserInfoResponse()
        except DoesNotExist as e:
            pass
        user = User()
        user.mobile = request.mobile
        user.nick_name = request.nickName
        user.password = pbkdf2_sha256.hash(request.password)
        user.save()
        user = User.get(User.mobile == request.mobile)
        return self.convert_user_to_rsp(user)

    @logger.catch()
    def UpdateUser(self, request, context):
        # 更新用户
        try:
            user = User.get(User.id == request.id)
            user.nick_name = request.nickName
            user.gender = request.gender
            user.birthday = date.fromtimestamp(request.birthday)
            user.save()
            return empty_pb2.Empty()
        except DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("用户不存在")
            return user_pb2.UserInfoResponse()

    @logger.catch()
    def CheckPassWord(self, request, context):
        # 检查密码
        return user_pb2.CheckResponse(success=pbkdf2_sha256.verify(request.password, request.encryptedPassword))
