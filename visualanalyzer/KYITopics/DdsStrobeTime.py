

#!/usr/local/bin/python3
# -*- coding: UTF-8 -*-



import sys, os
DDSApiPath = os.path.join(os.path.dirname(os.path.abspath(os.path.dirname(__file__))), 'DDSApi')
sys.path.insert(0, DDSApiPath)

import inspect
import getopt
import shutil
import getpass
import os, numpy, time, threading, glob
from multiprocessing.pool import ThreadPool
from DDSApi.DdsApi import *
from DdsHeader import *
from data_type import * #MyException
from KYITopics.KyiTopicHandler import *
import traceback



class DdsStrobeTimeHandler(KyiTopic):
    
    def __init__(self, dataParser):
        result = True
        msg = ""
        try:            
            super().__init__(dataParser)
            
            self.userName = "StrobeTime"
            self.topicName = "StrobeTime"            
            self.topicVersionMajor = "1"
            self.topicVersionMinor = "1"
            self.topicVersionPatch = "1"

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
            super().__del__()
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

    def parseAndUpdate(self):
        result = True
        msg = ""
        try:
            if self.recvCommand == "StrobeTime":
                params = self.recvParam.decode('utf-8').split(",")       
                
                deviceType = params[0] #jh-lee : 20230816 : PMD-35 : 토픽명을 데이터 기준으로 변경함으로 데이터에 디바이스 타입 추가
                volMin = params[2]
                volMax = params[3]
                onOffTimes = []
                for index in range(len(params)):
                    if index > 3:
                        onOffTimes.append(params[index])
                if(len(onOffTimes) % 2 == 1): #마지막 off 타임은 없을 수도 있으므로 더미로 채운다
                    onOffTimes.append(0)

                self._dataParser.updateDdsData(self.recvDomainId, self.recvTopic, self.recvCommand, deviceType, self.recvYear, self.recvMonth, self.recvDay, self.recvHour, self.recvMinute, self.recvSeconds, self.recvMilliconds, \
                    volMin, volMax, onOffTimes)     
        except MyException as ex:
            result = False
            msg = ex
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)            
                      



