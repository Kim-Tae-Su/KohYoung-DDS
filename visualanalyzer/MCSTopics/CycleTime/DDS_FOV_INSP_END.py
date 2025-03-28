






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
from MCSTopics.CycleTime.DDS_LANE_INSP_END import *
from MCSTopics.CycleTime.DDS_LANE_INSP_END import *
import traceback


class DdsFovInspEndHandler(McsTopic):
    
    def __init__(self, dataParser):
        result = True
        msg = ""
        try:            
            super().__init__(dataParser)
            
            self.userName = "VA"
            self.topicName = "VRUNACK"            
            self.topicVersionMajor = "1"
            self.topicVersionMinor = "1"
            self.topicVersionPatch = "1"

            self.fovCount=0
            self.fovNum=0

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
            if self.recvCommand == "GUItoMCS":
                params = self.recvParam.decode('utf-8').split()
                
                if(self.fovCount<(self.fovNum -1) and int(params[0]) < self.fovNum ):
                    #seqId = "FOV_INSP"
                    #userIndex = 1
                    #if(DdsLaneInspEndHandler.isDualLane==True):
                    #    seqId+=DdsLaneInspEndHandler.InspLane
                    
                    #self._dataParser.updateDdsData(self.recvDomainId, self.recvTopic, self.recvCommand,  self.recvYear, self.recvMonth, self.recvDay, self.recvHour, self.recvMinute, self.recvSeconds, self.recvMilliconds, seqId, userIndex) 
                   
                    seqId = "FOV_MOVE"
                    userIndex = 0
                    if(DdsLaneInspEndHandler.isDualLane==True):
                        seqId+=DdsLaneInspEndHandler.InspLane
                   
                    self._dataParser.updateDdsData(self.recvDomainId, self.recvTopic, self.recvCommand,  self.recvYear, self.recvMonth, self.recvDay, self.recvHour, self.recvMinute, self.recvSeconds, self.recvMilliconds, seqId, userIndex) 

                    self.fovCount+=1

                else:
                    #seqId = "FOV_INSP"
                    #userIndex = 1
                    #if(DdsLaneInspEndHandler.isDualLane==True):
                    #    seqId+=DdsLaneInspEndHandler.InspLane

                    
                    #self._dataParser.updateDdsData(self.recvDomainId, self.recvTopic, self.recvCommand,  self.recvYear, self.recvMonth, self.recvDay, self.recvHour, self.recvMinute, self.recvSeconds, self.recvMilliconds, seqId, userIndex) 

                    self.fovCount=0

            elif self.recvCommand == "MachineIdleStatus":
                params = self.recvParam.decode('utf-8').split()
                self.fovCount=0
                self.fovNum=int(params[0])

        except MyException as ex:
            result = False
            msg = ex
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)            
                      




