


#!/usr/local/bin/python3
# -*- coding: UTF-8 -*-

import sys, os
DDSApiPath = os.path.join(os.path.dirname(os.path.abspath(os.path.dirname(__file__))), 'DDSApi')
sys.path.insert(0, DDSApiPath)
from DDSApi.DdsApi import *
import inspect
import getopt
import shutil
import getpass
import os, numpy, time, threading, glob
from multiprocessing.pool import ThreadPool
from DdsHeader import *
from data_type import *#MyException
from abc import ABC, abstractmethod
import traceback



class KyiTopic(ABC):
    
    def __init__(self, dataParser):
        result = True
        msg = ""
        try:
            
            self.userName = ""
            self.topicName = ""
            self.domainId = 1
            self.topicVersionMajor = "1"
            self.topicVersionMinor = "1"
            self.topicVersionPatch = "1"

            self._dataParser = dataParser
        except MyException as ex:
            result = False
            msg = ex
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)


    def __del__(self):
        result = True
        msg = ""
        try:
            PRINT_INFO("Exit class.")
        except MyException as ex:
            result = False
            msg = ex
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)

    #DDS 인스턴스 생성 및 초기화
    def _initDds(self, userName, domainId, topicName, verMajor, verMinor, verPatch):
        result = True
        msg = ""
        try:
            self._ddsApiUserName = userName
            self._ddsApiDomainId = domainId
            self._ddsApiTopicName = topicName
            self._ddsApiVerMajor = verMajor
            self._ddsApiVerMinor = verMinor
            self._ddsApiVerPatch = verPatch
            self._ddsApiHandle = DdsApiHandler(False, self._ddsApiUserName, self._ddsApiDomainId, self._ddsApiTopicName, self._ddsApiVerMajor, self._ddsApiVerMinor, self._ddsApiVerPatch, self._ddsRecv)
        except MyException as ex:
            result = False
            msg = ex
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)   

    @abstractmethod
    def parseAndUpdate(self):
        pass

    #DDS 데이터 수신
    def _ddsRecv(self, eventCode, domainId, topic, publishTime, subscribeTime, command, parameter, parameterSize, data, dataSize, verMajor, verMinor, verPatch):
        result = True
        msg = ""
        try:
            PRINT_INFO('dds data received : {} {} {} {} '.format(eventCode, domainId, topic, publishTime))
            #logger('dds data received : {} {} {} {} '.format(eventCode, domainId, topic, publishTime))

            if parameterSize ==0:
                parameter = ''

            commData = 'dds data received : {} {} {} {} {} {} {} {} {} {} {} {} {} '.format(eventCode, domainId, topic, publishTime, subscribeTime, command, parameter, parameterSize, data, dataSize, verMajor, verMinor, verPatch)

            if eventCode == 1:    
                self.recvYear = publishTime[0:4].decode('utf-8')
                self.recvMonth = publishTime[5:7].decode('utf-8')
                self.recvDay = publishTime[8:10].decode('utf-8')
                self.recvHour = publishTime[11:13].decode('utf-8')
                self.recvMinute = publishTime[14:16].decode('utf-8')
                self.recvSeconds = publishTime[17:19].decode('utf-8')
                self.recvMilliconds = publishTime[20:23].decode('utf-8')
                
                self.recvTopic = topic.decode('utf-8')
                self.recvCommand = command.decode('utf-8')
                self.recvDomainId = domainId
                self.recvParam = parameter
                self.parseAndUpdate()

        except MyException as ex:
            result = False
            msg = ex
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)


    def initHandler(self):

        result = True
        msg = ""
        try:
            self._initDds(self.userName, self.domainId, self.topicName, self.topicVersionMajor, self.topicVersionMinor, self.topicVersionPatch) #jh-lee : 20230816 : PMD-35 : 토픽명을 데이터 기준으로 변경함으로 디바이스 이름 제거
        except MyException as ex:
            result = False
            msg = ex
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)
                
                
    def uninitHandler(self):
        result = True
        msg = ""
        try:
            pass
            #self.thread.stop
        except MyException as ex:
            result = False
            msg = ex
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)
