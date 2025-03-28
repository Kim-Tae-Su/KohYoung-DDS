




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



class DdsPcbOutNextStatusHandler(McsTopic):
    
    def __init__(self, dataParser):
        result = True
        msg = ""
        try:            
            super().__init__(dataParser)
            
            self.userName = "VA"
            self.topicName = "PCB_OUT_NEXT_STATUS"            
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
            # params = self.recvParam.decode('utf-8').split(",")  
           
            valid_commands = { "FrontLane_Entry_PCB_Status" : "_F_EN", 
                               "FrontLane_Work_PCB_Status"  : "_F_WK", 
                               "FrontLane_Exit_PCB_Status"  : "_F_EX",
                               "RearLane_Entry_PCB_Status"  : "_R_EN",
                               "RearLane_Work_PCB_Status"   : "_R_WK",
                               "RearLane_Exit_PCB_Status"   : "_R_EX", }
            for key, value in valid_commands.items():
                if self.recvCommand == key:
                    seqId = self.recvTopic+value
                    userIndex = int(self.recvParam)

                    self._dataParser.updateDdsData(self.recvDomainId, self.recvTopic, self.recvCommand,  self.recvYear, self.recvMonth, self.recvDay, self.recvHour, self.recvMinute, self.recvSeconds, self.recvMilliconds, seqId, userIndex)  
                    break
 
        except MyException as ex:
            result = False
            msg = ex
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)            
                      




