





#!/usr/local/bin/python3
# -*- coding: UTF-8 -*-

from DDSApi.DdsApi import *
import inspect
import getopt
import shutil
import getpass
import os, numpy, time, threading, glob
from multiprocessing.pool import ThreadPool
from DdsHeader import *
from data_type import *#MyException

from MCSTopics.McsTopicHandler import *
import traceback



class DdsTurnaroundEndHandler(McsTopic):
    
    def __init__(self, dataParser):
        result = True
        msg = ""
        try:            
            super().__init__(dataParser)
            
            self.userName = "VA"
            self.topicName = "EXTOUT"            
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
            if self.recvCommand == "MCStoGUI":
                if isinstance(self.recvParam, bytes):
                    params = self.recvParam.decode('utf-8').split()
                
                    seqId = "TURNAROUND_TIME"+params[0]
                else:
                    seqId = "TURNAROUND_TIME"
                userIndex = 1

                
                self._dataParser.updateDdsData(self.recvDomainId, self.recvTopic, self.recvCommand,  self.recvYear, self.recvMonth, self.recvDay, self.recvHour, self.recvMinute, self.recvSeconds, self.recvMilliconds, seqId, userIndex) 
        except MyException as ex:
            result = False
            msg = ex
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)            
                      




