#!/usr/local/bin/python3
# -*- coding: UTF-8 -*-

# DB 제어 관련 super class

from if_db import *
from define import *
from libs.debug import *
from data_type import *
import traceback


class CDBHandler(IDBHandler):
    def __init__(self):
        # 자식 class 에서 재정의 필요
        self.recv_packet_buf = None
        self.all_packet_buf = None
        self.show_packet_buf = None

    # 자식 class 의 함수를 호출하게 된다
    @abstractmethod
    def add_packet(self, packet, packet_type):
        pass

    # 자식 class 의 함수를 호출하게 된다
    @abstractmethod
    def clear_packet_buf(self, packet_type):
        pass

    ##########################################################################################
    # Module buffer 에 data 입력
    # param :
    #   data        입력 data
    # return : None
    ##########################################################################################
    def set_data(self, data):
        result = True
        msg = ""
        try:
            self.add_packet(data, PACKET_RECV)
            self.add_packet(data, PACKET_ALL)
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)

    ##########################################################################################
    # Return buffer
    # param :
    #   type        가져올 buffer type
    # return : buffer
    ##########################################################################################
    def get_buffer(self, packet_type):
        result = True
        msg = ""
        try:
            ret = None
            if packet_type == PACKET_RECV:
                ret = self.recv_packet_buf
            elif packet_type == PACKET_ALL:
                ret = self.all_packet_buf
            elif packet_type == PACKET_SHOW:
                ret = self.show_packet_buf
            else:
                raise MyException(f'wrong packet type {packet_type}')
            return ret
        except MyException as ex:
            result = False
            msg = ex                
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)

    ##########################################################################################
    # Clear buffer
    # param :
    #   type        삭제할 buffer type
    # return : None
    ##########################################################################################
    def clear_buffer(self, packet_type = PACKET_ALL_TYPE):
        result = True
        msg = ""
        try:
            if packet_type == PACKET_ALL_TYPE:
                self.clear_packet_buf(PACKET_RECV)
                self.clear_packet_buf(PACKET_ALL)
                self.clear_packet_buf(PACKET_SHOW)
            else:
                self.clear_packet_buf(packet_type)
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)

    ##########################################################################################
    # buffer 가 empty 인지
    # param :
    #   type        buffer type
    # return : empty 면 True 아니면 False
    ##########################################################################################
    def is_buffer_empty(self, packet_type):
        result = True
        msg = ""
        try:
            ret = False
            if packet_type == PACKET_RECV:                
                if len(self.recv_packet_buf) > 0:
                    ret = True
            elif packet_type == PACKET_ALL:
                if len(self.all_packet_buf) > 0:
                    ret = True
            elif packet_type == PACKET_SHOW:
                if len(self.show_packet_buf) > 0:
                    ret = True
            else:
                raise MyException(f'wrong packet type {packet_type}')
            return ret
        except MyException as ex:
            result = False
            msg = ex                
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)