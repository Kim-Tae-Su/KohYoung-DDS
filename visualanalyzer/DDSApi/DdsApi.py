
#!/usr/local/bin/python3
# -*- coding: UTF-8 -*-



import sys, os
#DDSApiPath = os.path.join(os.path.dirname(os.path.abspath(os.path.dirname(__file__))), 'DDSApi')
#sys.path.insert(0, DDSApiPath)

import inspect
import getopt
import shutil
import getpass

from ctypes import*
from time import sleep
import time
from datetime import datetime
import ctypes
from threading import Thread, Lock
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import  QApplication, QMainWindow, QWidget, QDesktopWidget
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import * #QDate, Qt
from PyQt5 import *
from libs.debug import *
from data_type import * #MyException
import traceback




############################################################
#C++ dll 선언
import ctypes
ddsApi = ctypes.CDLL('C:/Kohyoung/DDS/Bin/DdsApiForC.dll') #*.lib 파일까지 같이 업데이트 되어야 정상 적용된다


class RecvTopicInfo(Structure) :
    _pack_ = 8
    _fields_ = [("eventCode_", c_int),
                 ("domainId_", c_int),
                 ("topic_", c_char_p),
                 ("publishTime_", c_char_p),
                 ("subscribeTime_", c_char_p),
                 ("command_", c_char_p),
                 ("parameter_", c_char_p),
                 ("parameterSize_", c_int),
                 ("data_", c_char_p),
                 ("dataSize_", c_int),
                 ("verMajor_", c_char_p),
                 ("verMinor_", c_char_p),
                 ("verPatch_", c_char_p),
                 ("systemId_", c_char_p),
                 ("systemName_", c_char_p)]


HDDSAPI = ctypes.c_void_p
ResultCode = ctypes.c_int
print_callback = ctypes.CFUNCTYPE(None, ResultCode, ctypes.c_char_p, ctypes.c_int)
topic_callback = ctypes.CFUNCTYPE(None, ctypes.c_void_p)



class DdsApiHandler:
        

    PUBLISHER = True
    SUBSCRIBER = False

    RC_ERROR = 0
    RC_OK = 1             
    RC_WARNING = 2        
    RC_BAD_ANY_CAST = 3     
    RC_EXCEPTION = 4
    RC_UNKNOWN_EXCEPTION = 5
    RC_UNKNOWN_COMMAND = 6



    def __init__(self, isPub, userName, domainId, topicName, verMajor, verMinor, verPatch, dataRecvCallback):

        result = True
        msg =""
        
        #self.outputView = outputView;

        try:
            PRINT_INFO("initialize for {} {} {}..".format(userName, domainId, topicName))

            self.domainId = domainId
            self.topicName = topicName
            self.userName = userName
            self.isPublisher = isPub
            
            self.recvTopics = []

            self.ddsRecv = dataRecvCallback

            self.exitThread = False

            #모듈의 인스턴스를 생성한다
            self.createDdsApiInstance = ddsApi.createDdsApiInstance
            self.createDdsApiInstance.argtypes = [ctypes.c_bool]
            self.createDdsApiInstance.restype = HDDSAPI

            #모듈의 인스턴스를 제거한다
            self.deleteDdsApiInstance = ddsApi.deleteDdsApiInstance
            self.deleteDdsApiInstance.argtypes = [HDDSAPI]

            #모듈의 참여타입(발행/구독)을 조회한다.
            self.isPublisher = ddsApi.isPublisher
            self.isPublisher.argtypes = [HDDSAPI]
            self.isPublisher.restype = ctypes.c_bool

            #모듈을 초기화 한다
            self.initialize = ddsApi.initialize
            self.initialize.argtypes = [HDDSAPI, ctypes.c_char_p, ctypes.c_uint32, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint32]
            self.initialize.restype = ctypes.c_bool

            #모듈의 인스턴스를 생성한다
            self.instance = ddsApi.createDdsApiInstance(isPub)

            #모듈로 부터 상태 수신을 위한 인터페이스를 등록한다
            self.registerDdsApiPrintEvent = ddsApi.registerDdsApiPrintEvent
            ddsApiPrintEventProtoType = CFUNCTYPE(None, c_int, c_char_p, c_int)
            self.registerDdsApiPrintEvent.argtypes = [HDDSAPI, ctypes.c_char_p, ctypes.c_uint, ctypes.c_char_p, ddsApiPrintEventProtoType]
            self.registerDdsApiPrintEvent.restype = None
            self.ddsApiPrintEvent = ddsApiPrintEventProtoType(self.printEventCallback)
            self.registerDdsApiPrintEvent(HDDSAPI(self.instance), bytes(userName, encoding="utf-8"), int(domainId), bytes(topicName, encoding="utf-8"), self.ddsApiPrintEvent)

            #모듈로 부터 토픽 수신을 위한 인터페이스를 등록한다
            if isPub == False:
                self.registerDdsApiTopicEvent = ddsApi.registerDdsApiTopicEvent
                ddsApiTopicEventProtoType = CFUNCTYPE(None, POINTER(RecvTopicInfo))
                self.registerDdsApiTopicEvent.argtypes = [HDDSAPI, ctypes.c_char_p, ctypes.c_uint, ctypes.c_char_p, ddsApiTopicEventProtoType]
                self.registerDdsApiTopicEvent.restype = None
                self.ddsApiTopicEvent = ddsApiTopicEventProtoType(self.topicEventCallback)
                self.registerDdsApiTopicEvent(HDDSAPI(self.instance), bytes(userName, encoding="utf-8"), int(domainId), bytes(topicName, encoding="utf-8"), self.ddsApiTopicEvent)
            

            #
            #self.removeDdsApiPrintEvent = ddsApi.removeDdsApiPrintEvent
            #self.removeDdsApiPrintEvent.argtypes = [HDDSAPI, ctypes.c_char_p, ctypes.c_uint, ctypes.c_char_p, print_callback]
            #self.removeDdsApiPrintEvent.restype = ctypes.c_bool
            #self.removeDdsApiPrintEvent(self.instance, userName, domainId, topicName, print_callback(print_event_callback))
            ##ddsApi.removeDdsApiPrintEvent(HDDSAPI(self.instance), bytes(userName, encoding="utf-8"), int(domainId), bytes(topicName, encoding="utf-8"), self.ddsApiPrintEvent)
                        


            #모듈에 등록된 이벤트를 모두 제거한다
            self.removeDdsApiPrintEvents = ddsApi.removeDdsApiPrintEvents
            self.removeDdsApiPrintEvents.argtypes = [HDDSAPI]
            self.removeDdsApiPrintEvents.restype = ctypes.c_bool

            

            #모듈에 등록된 이벤트를 모두 제거한다
            self.removeDdsApiTopicEvents = ddsApi.removeDdsApiTopicEvents
            self.removeDdsApiTopicEvents.argtypes = [HDDSAPI]
            self.removeDdsApiTopicEvents.restype = ctypes.c_bool


            #모듈을 해제한다
            self.uninitialize = ddsApi.uninitialize
            self.uninitialize.argtypes = [HDDSAPI]
            self.uninitialize.restype = ctypes.c_bool

            #토픽 수신자가 있을때까지 대기한다
            self.waitServiceAvailable = ddsApi.waitServiceAvailable
            self.waitServiceAvailable.argtypes = [HDDSAPI, ctypes.c_uint32]
            self.waitServiceAvailable.restype = ctypes.c_bool

            #토픽을 발행한다
            self.publishTopic = ddsApi.publishTopic
            self.publishTopic.argtypes = [HDDSAPI, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint32, ctypes.c_char_p, ctypes.c_uint32, ctypes.c_bool, ctypes.c_uint32, ctypes.c_char_p]
            self.publishTopic.restype = ctypes.c_bool

            #공유메모리 주소와 크기를 조회한다
            self.getDataMemory = ddsApi.getDataMemory
            self.getDataMemory.argtypes = [HDDSAPI, ctypes.c_void_p, ctypes.c_uint32]
            self.getDataMemory.restype = ctypes.c_bool
            
            
            #옵션설정 인터페이스
            self.setConfig = ddsApi.setConfig
            self.setConfig.argtypes = [HDDSAPI, ctypes.c_char_p, ctypes.c_char_p]
            self.setConfig.restype = ctypes.c_bool


            #옵션 설정
            self.setConfig(self.instance, bytes("DiscoveryFilter", encoding="utf-8"), bytes("FilterDifferentHost", encoding="utf-8"))


            #DDS 초기화
            result = self.initialize(self.instance, bytes(userName, encoding="utf-8"), int(domainId), bytes(topicName, encoding="utf-8"), bytes(verMajor, encoding="utf-8"), bytes(verMinor, encoding="utf-8"), bytes(verPatch, encoding="utf-8"), 0)

            
            #수신쓰레드 초기화
            self.lock = Lock()
            self.exitThread = False
            self.recvThreadHandle = Thread(target=self.ddsReceive,args=(self,))
            self.recvThreadHandle.daemon = True

            self.event_topic_receive_wait = threading.Event()
        except MyException as ex:
            result = False
            msg = ex
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)
            else:
                self.run()


    def __del__(self):
        result = True
        msg = ""
        try:
            PRINT_INFO("Exit class.")
            self.uninitialize(HDDSAPI(self.instance))
            
            #exitThread = True
            self.recvThreadHandle.join()
        except MyException as ex:
            result = False
            msg = ex
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)

    def run(self):
        result = True
        msg = ""
        try:
            QtCore.QCoreApplication.processEvents()
            #포트 오픈
            #self.serialHandle.Open()

            #수신 쓰레드 시작
            self.recvThreadHandle.start()
            #self.recvThreadHandle.join()
        except MyException as ex:
            result = False
            msg = ex
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)

    def sendTopic(self, command, parameter, parameterSize, data, dataSize, useSharedMemory, timeout, destName):
        result = True
        msg = ""
        try:
            QtCore.QCoreApplication.processEvents()
            result = self.publishTopic(HDDSAPI(self.instance), bytes(command, encoding="utf-8"), bytes(parameter, encoding="utf-8"), int(parameterSize), bytes(data, encoding="utf-8"), int(dataSize), int(useSharedMemory), int(timeout), bytes(destName, encoding="utf-8"))
        except MyException as ex:
            result = False
            msg = ex
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)


    def printEventCallback(self, resultCode, message, size):
        result = True
        msg = ""
        try:
            if int(resultCode) == DdsApiHandler.RC_OK:
               print(message.decode())
            PRINT_DEBUG("{}".format(message))
        except MyException as ex:
            result = False
            msg = ex
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)


    def topicEventCallback(self, topicInfo):
        result = True
        msg = ""
        try:
            #print("TopicCallback. {} {} {} {} {} {} {} {} {} {} {} {} {}".format(topicInfo.contents.eventCode_, topicInfo.contents.domainId_, topicInfo.contents.topic_, topicInfo.contents.publishTime_, topicInfo.contents.subscribeTime_, topicInfo.contents.command_, topicInfo.contents.parameter_, topicInfo.contents.parameterSize_, topicInfo.contents.data_, topicInfo.contents.dataSize_, topicInfo.contents.verMajor_, topicInfo.contents.verMinor_, topicInfo.contents.verPatch_)) 
            PRINT_DEBUG("TopicCallback. {} {} {} {} {} {}".format(topicInfo.contents.eventCode_, topicInfo.contents.domainId_, topicInfo.contents.topic_,  topicInfo.contents.publishTime_, topicInfo.contents.subscribeTime_, topicInfo.contents.command_))   
            #print("TopicCallback. {} {} {} {} {} {} {}".format(topicInfo.contents.parameter_, topicInfo.contents.parameterSize_, topicInfo.contents.data_, topicInfo.contents.dataSize_, topicInfo.contents.verMajor_, topicInfo.contents.verMinor_, topicInfo.contents.verPatch_))   
            
            if topicInfo.contents.parameterSize_ > 0 :
                PRINT_DEBUG("TopicCallback. {} ".format( topicInfo.contents.parameter_))   
            PRINT_DEBUG("TopicCallback. {} ".format( topicInfo.contents.parameterSize_))   

            param = ''
            data = ''
            if topicInfo.contents.parameterSize_ > 0:
                param = topicInfo.contents.parameter_
           
            if topicInfo.contents.dataSize_ > 0:
                data = topicInfo.contents.data_

            rcv = [topicInfo.contents.eventCode_, topicInfo.contents.domainId_, topicInfo.contents.topic_, \
                topicInfo.contents.publishTime_, topicInfo.contents.subscribeTime_, topicInfo.contents.command_, param, \
                topicInfo.contents.parameterSize_, data, topicInfo.contents.dataSize_, topicInfo.contents.verMajor_, \
                topicInfo.contents.verMinor_, topicInfo.contents.verPatch_, topicInfo.contents.systemId_, topicInfo.contents.systemName_]
                        
            self.lock.acquire()
            self.recvTopics.append(rcv)
            PRINT_DEBUG('recvTopics size : {}'.format(len(self.recvTopics)))
            self.lock.release()

            self.event_topic_receive_wait.set()
        except MyException as ex:
            result = False
            msg = ex
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)

    def ddsReceive(self, handle):
        result = True
        msg = ""
        while not self.exitThread:
            QtCore.QCoreApplication.processEvents()
            try:
                # thread 동작을 polling 에서 event 수신 시 처리로 바꾼다. -> 실시간 그래프 성능 개선 효과
                self.event_topic_receive_wait.wait()

                curData = []
                handle.lock.acquire() #뮤텍스 잠금l
                if len(handle.recvTopics) > 0:
                    curData = handle.recvTopics[0]
                    #print('recvTopics size in thread : {}'.format(len(self.recvTopics)))
                    del handle.recvTopics[0]
                handle.lock.release() #뮤텍스 해제

                if len(curData) > 0:
                    #handle.ddsRecv(eventCode, domainId, topic, publishTime, subscribeTime, command, parameter, parameterSize, data, dataSize, verMajor, verMinor, verPatch)
                        handle.ddsRecv(curData[0], curData[1], curData[2], curData[3], curData[4], curData[5], curData[6], \
                            curData[7], curData[8], curData[9], curData[10], curData[11], curData[12]) 
                        #curData[13] 은 system ID 로 현재 user는 사용하지 않음
                        #curData[14] 은 system Name 으로 현재 user는 사용하지 않음
                else:
                    self.event_topic_receive_wait.clear()

            except MyException as ex:
                result = False
                msg = ex
            except Exception as ex:
                result = False
                msg = "{}".format(traceback.format_exc())
            finally:
                if result == False:
                    PRINT_ERR(msg)