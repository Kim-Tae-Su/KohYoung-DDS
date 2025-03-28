




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



class DdsSmemaHandler(McsTopic):
    
    def __init__(self, dataParser):
        result = True
        msg = ""
        try:            
            super().__init__(dataParser)
            
            self.userName = "VA"
            self.topicName = "clrSmem"            
            self.topicVersionMajor = "1"
            self.topicVersionMinor = "1"
            self.topicVersionPatch = "1"

            self.frontlane_psmemain=0
            self.frontlane_psmemaout=0
            self.frontlane_nsmemain=0
            self.frontlane_nsmemaout=0
            self.frontlane_ngbuffer=0

            self.frontlane_smema_list=[self.frontlane_psmemain, self.frontlane_psmemaout, self.frontlane_nsmemain, self.frontlane_nsmemaout, self.frontlane_ngbuffer]

            self.duallane_psmemain=0
            self.duallane_psmemaout=0
            self.duallane_nsmemain=0
            self.duallane_nsmemaout=0
            self.duallane_ngbuffer=0
            
            self.duallane_smema_list=[self.duallane_psmemain, self.duallane_psmemaout, self.duallane_nsmemain, self.duallane_nsmemaout, self.duallane_ngbuffer]

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
                params = self.recvParam.decode('utf-8').split()
                if len(params) > 1:
                    smema_list = self.duallane_smema_list if int(params[1]) == 1 else self.frontlane_smema_list
                else:
                    smema_list = self.frontlane_smema_list

                smema_name=["PSMEMA_IN", "PSMEMA_OUT", "NSMEMA_IN", "NSMEMA_OUT", "NG_BUFFER"]

                for i in range(len(smema_name)):
                    if smema_list[i]!=int(params[0][i]):
                        seqId=smema_name[i]

                        smema_list[i] = int(params[0][i])

                        if int(params[0][i])==0:
                            userIndex=1
                        else:
                            userIndex=0
                        break
                if(len(params)>1):
                  seqId+=params[1]

                
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
                      




