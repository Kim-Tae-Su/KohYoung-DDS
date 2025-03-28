
#!/usr/local/bin/python3
# -*- coding: UTF-8 -*-


from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from libs.debug import *
import copy
from define import *
from data_type import *
from db_handler import *
# # 마우스 휠로 확대/축소 동작 가능, Agg 는 안됨
import matplotlib
matplotlib.use('QtAgg')
from figure_canvas import *
import traceback


# KYI data(topic) 처리 handler

class CGrabStartData(CDdsDataHeader): 
    def __init__(self, domain = 0, topic = "", cmd = "", time: datetime = 0, seqId = 0, userIndex = 0, isWait = False, grabMode = "", userMemory = "", userMemorySize = 0):
        super().__init__(domain, topic, cmd, time)
        self.seqId = seqId
        self.userIndex = userIndex
        self.isWait = isWait
        self.grabMode = grabMode
        self.userMemory = userMemory
        self.userMemorySize = userMemorySize
        return None

class CGrabEndData(CDdsDataHeader): 
    def __init__(self, domain = 0, topic = "", cmd = "", time: datetime = 0, seqId = 0, userIndex = 0, spanTime = 0):
        super().__init__(domain, topic, cmd, time)
        self.seqId = seqId
        self.userIndex = userIndex
        self.spanTime = spanTime
        return None

class CGrabberStartData(CDdsDataHeader): 
    def __init__(self, domain = 0, topic = "", cmd = "", time: datetime = 0, seqId = 0):
        super().__init__(domain, topic, cmd, time)
        self.seqId = seqId
        return None

class CGrabberEndData(CDdsDataHeader): 
    def __init__(self, domain = 0, topic = "", cmd = "", time: datetime = 0, seqId = 0, seqState = 0):
        super().__init__(domain, topic, cmd, time)
        self.seqId = seqId
        self.seqState = seqState        # 0 : No error, 1 : Error
        return None

# GrabberCommandStart, GrabberCommandEnd, GrabberReinitStart, GrabberReinitEnd, GrabDoneStart, GrabDoneEnd 에서 공통으로 사용
class CGrabCommonData(CDdsDataHeader):
    def __init__(self, domain = 0, topic = "", cmd = "", time: datetime = 0, seqId = 0, userIndex = 0):
        super().__init__(domain, topic, cmd, time)
        self.seqId = seqId
        self.userIndex = userIndex
        return None

class CKyi(CDBHandler, CFigureCanvasHandler):
    def __init__(self):
        CFigureCanvasHandler.__init__(self)
        # 수신 packet, show list 로 옮겨진다
        # self.recv_packet_buf: list[CKyiData] = list()
        self.recv_packet_buf = list()
        # 모든 수신 packet
        self.all_packet_buf = list()
        # 그래프로 출력할 packet
        self.show_packet_buf = list()
        # error seq 구분
        self.error_seq: list[str] = list()
        self.target = TARGET_KYI
        self.data_file = "./db/kyi.json"
        self.fig_width_size_inch = 14
        self.fig_height_size_inch = 7
        return None

    ##########################################################################################
    # Add packet of cycle time
    # param :
    #   packet         packet of cycle time
    #   packet_type    packet type
    # return : None
    ##########################################################################################
    def add_packet(self, packet, packet_type):
        result = True
        msg = ""
        try:
            if packet_type == PACKET_RECV:
                self.recv_packet_buf.append(packet)
            elif packet_type == PACKET_ALL:
                self.all_packet_buf.append(packet)
            elif packet_type == PACKET_SHOW:
                self.show_packet_buf.append(packet)
            else:
                raise MyException(f'wrong packet type {packet_type}')
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
    # Clear packet buffer
    # param :
    #   packet_type    packet type    
    ##########################################################################################
    def clear_packet_buf(self, packet_type):
        result = True
        msg = ""
        try:
            if packet_type == PACKET_RECV:
                self.recv_packet_buf.clear()
            elif packet_type == PACKET_ALL:
                self.all_packet_buf.clear()
            elif packet_type == PACKET_SHOW:
                self.show_packet_buf.clear()
            else:
                raise MyException(f'wrong packet type {packet_type}')
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
    # datetime, name 으로 packet 을 찾는다
    # param :
    #   datetime_obj    datetime
    #   name            찾을 data name
    # return : 찾으면 packet, 못 찾으면 None
    ##########################################################################################    
    def get_packet(self, datetime_obj, name):
        result = True
        msg = ""
        try:
            for packet in self.all_packet_buf:
                if packet.datetime == datetime_obj and packet.topic == name:
                    return packet
            raise MyException(f'{datetime_obj} {name} is not exist')
        except MyException as ex:
            result = False
            msg = ex
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)
                return None