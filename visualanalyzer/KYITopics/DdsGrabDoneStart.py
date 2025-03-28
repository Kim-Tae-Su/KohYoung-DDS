

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

from KYITopics.KyiTopicHandler import *
import traceback



class DdsGrabDoneStartHandler(KyiTopic):
    
    def __init__(self, dataParser):
        result = True
        msg = ""
        try:            
            super().__init__(dataParser)
            
            self.userName = "GrabDoneStart"
            self.topicName = "GrabDoneStart"            
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
            if self.recvCommand == "GrabDoneStart":
                params = self.recvParam.decode('utf-8').split(",")                
                 
                seqId = params[0]
                userIndex = params[1]

                self._dataParser.updateDdsData(self.recvDomainId, self.recvTopic, self.recvCommand, self.recvYear, self.recvMonth, self.recvDay, self.recvHour, self.recvMinute, self.recvSeconds, self.recvMilliconds, \
                    seqId, userIndex)   
        except MyException as ex:
            result = False
            msg = ex
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)            
                      






