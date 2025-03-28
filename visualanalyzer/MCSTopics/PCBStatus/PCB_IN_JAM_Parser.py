




#!/usr/local/bin/python3
# -*- coding: UTF-8 -*-


# 외부 data 를 parsing 하여 처리할 수 있는 data format 으로 변경
#
# data flow
#   KYI, MCS -> DDS -> PARSER -> DB
#   KYI, MCS -> DDS -> PARSER -> Handler

from handle_json import *
from datetime import datetime
from MCSTopics.PCBStatus.DDS_PCB_IN_JAM import * 
from data_export_thread import CDataExportThread
from libs.debug import *
from data_type import MyException
from define import *
from mcs_pcb_status_handler import *
# from db_handler import *
import traceback

DATETIME_FORMAT = "%Y/%m/%d_%H:%M:%S:%f"


class CPcbInJamParser(CDataExportThread, CJasonManager):
    def __init__(self, handle : CMcsPcbStatus):
        result = True
        msg = ""
        try:
            CDataExportThread.__init__(self) 
            CJasonManager.__init__(self, name="{}".format(self.__class__.__name__))  

            self._db = handle
            self._ddsHandler = None 
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
            if self._ddsHandler:
                self.uninitDdsHandler() #jh-lee : 20230816 : PMD-35 : 토픽명을 데이터 기준으로 변경함으로 디바이스 이름 제거
        except MyException as ex:
            result = False
            msg = ex
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)

    # 객체 삭제 전 객체 내 thread 먼저 종료해야한다
    def finalize(self):
        # thread loop 종료시키기
        self.exit_thread = True
        # thread 종료 대기
        self.export_thread.join()        

    # jhlee : 20230817 : DDS 핸들러 초기화
    def initDdsHandler(self):
        result = True
        msg = ""
        try:
            self._ddsHandler = DdsPcbInJamHandler(self)
            self._ddsHandler.initHandler()
        except MyException as ex:
            result = False
            msg = ex
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)

    # jhlee : 20230817 : DDS 핸들러 해제
    def uninitDdsHandler(self):
        result = True
        msg = ""
        try:
            if self._ddsHandler:
                self._ddsHandler.uninitHandler() 
        except MyException as ex:
            result = False
            msg = ex
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)

    def updateDdsData(self, domain, topic, cmd, year, month, day, hour, minute, seconds, millisconds, seqId, userIndex):
        result = True
        msg = ""
        try:
            data = CMcsPcbStatusData(
                domain,
                topic,
                cmd,
                datetime.strptime("{}/{}/{}_{}:{}:{}:{}".format(year, month, day, hour, minute, seconds, millisconds), DATETIME_FORMAT),
                seqId, userIndex)
            
            # parsing 된 data 를 module 에 추가
            self._db.add_packet(data, PACKET_RECV)
            self._db.add_packet(data, PACKET_ALL)   
                            
            # thread 에서 data 를 file 로 export 한다
            self.add_data(data)
        except MyException as ex:
            result = False
            msg = ex
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)

           
    def export_data(self, pcb_data: CMcsPcbStatusData):
        result = True
        msg = ""
        try:
            data = list()
            data = [{
                'domain': pcb_data.domain,
                'topic': pcb_data.topic,
                'cmd': pcb_data.cmd,
                'datetime': pcb_data.datetime.strftime(DATETIME_FORMAT),
                'status': pcb_data.status,
                'state': pcb_data.state
            }]

            self.write_file(data, self._db.data_file, MODE_APPEND)
        except MyException as ex:
            result = False
            msg = ex
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result is False:
                PRINT_ERR(msg)