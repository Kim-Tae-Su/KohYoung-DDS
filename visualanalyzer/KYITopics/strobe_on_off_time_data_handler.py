
#!/usr/local/bin/python3
# -*- coding: UTF-8 -*-


# 외부 data 를 해당 module에서 처리할 수 있는 data format 으로 변경
# data 를 DB 로 export
# DB 에서 data 를 load 하여 module 에 전달
# data flow
#   KYI, MCS -> DDS -> Data Handler -> DB
#   KYI, MCS -> DDS -> Data Handler -> Module

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
KYITopicsPath = os.path.join(os.path.dirname(os.path.abspath(os.path.dirname(__file__))), 'KYITopics')
sys.path.insert(0, KYITopicsPath)

from handle_json import *
from strobe_on_off_time_handler import *
from datetime import datetime
from KYITopics.DdsStrobeTime import *
from data_export_thread import CDataExportThread
from libs.debug import *
from data_type import MyException
import traceback


DATETIME_FORMAT = "%Y/%m/%d_%H:%M:%S:%f"


class CStrobeOnOffTimeDataHandler(CDataExportThread, CJasonManager):
    def __init__(self, handle:CStrobeOnOffTime):
        result = True
        msg = ""
        try:
            CDataExportThread.__init__(self) 
            CJasonManager.__init__(self, name="{}".format(self.__class__.__name__))  

            self._db = handle
           
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
        #self.export_thread.join()        

    # jhlee : 20230817 : StrobeTime 용 DDS 핸들러 초기화
    def initDdsHandler(self):
        result = True
        msg = ""
        try:
            self._ddsHandler = DdsStrobeTimeHandler(self) #jh-lee : 20230816 : PMD-35 : 토픽명을 데이터 기준으로 변경함으로 디바이스 이름 제거
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

    # jhlee : 20230817 : StrobeTime 용 DDS 핸들러 해제
    def uninitDdsHandler(self):
        result = True
        msg = ""
        try:
            self._ddsHandler.uninitHandler() #jh-lee : 20230816 : PMD-35 : 토픽명을 데이터 기준으로 변경함으로 디바이스 이름 제거
        except MyException as ex:
            result = False
            msg = ex
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)

    # jhlee : 20230817 : StrobeTime 용 스트로브 On/Off타입 업데이트
    # jh-lee : 20230816 : PMD-35 : 토픽명을 데이터 기준으로 변경함으로 디바이스 타입 추가
    def updateDdsData(self, domain, topic, cmd, year, month, day, hour, minute, seconds, millisconds, voltageMin, voltageMax, onOffTimes):
        result = True
        msg = ""
        try:
            # DDS 로부터 받은 data를 strobe on off time data type 에 맞게 parsing
            data = CStrobeOnOffTimeData(
                domain,
                topic,
                cmd,
                datetime.strptime("{}/{}/{}_{}:{}:{}:{}".format(year, month, day, hour, minute, seconds, millisconds), DATETIME_FORMAT),
                int(len(onOffTimes) / 2),  # on/off 하나의 셋으로 카운트
                int(voltageMax),
                int(voltageMin),
                deviceType)
            
            data.clear_data()
            for index in range(0, len(onOffTimes), 2):
                new_time = COnOffTime(int(onOffTimes[index]), int(onOffTimes[index + 1]))
                data.append_data(new_time)
            
            # IF 통해 module 에 data 전달
            # parsing 된 data 를 module 에 추가
            self._db.set_data(data)

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

    ##########################################################################################
    # parsing 된 data 를 export
    #   json file 로 만든다
    # return : None
    ##########################################################################################
    def export_data(self, time_data: CStrobeOnOffTimeData):
        data = list()

        data.append({
            'domain': time_data.domain,
            'topic': time_data.topic,
            'cmd': time_data.cmd,
            'datetime': time_data.datetime.strftime(DATETIME_FORMAT),
            'count': time_data.count,
            'on_time_vol': time_data.on_time_vol,
            'off_time_vol': time_data.off_time_vol,
            'device': time_data.device
            })

        # 현재 추가한(마지막) 리스트 요소에 time 항목 추가
        data[-1]['time'] = list()
        for time in time_data.on_off_time:
            new_time = {"on_time": time.on_time, "off_time": time.off_time}
            data[-1]['time'].append(new_time)

        # write_file(data, self._db.data_file, MODE_OVERWRITE)
        self.write_file(data, self._db.data_file, MODE_APPEND)
        return None

    ##########################################################################################
    # json file 로부터 data 를 읽어 CStrobeOnOffTime time 에 load
    # return : None
    ##########################################################################################
    def load(self):
        data_list = CJasonManager.read_file(self._db.data_file)
        
        # set data to strobe on off time module
        for data in data_list:
            cmd = CStrobeOnOffTimeData(
                data['domain'],
                data['topic'],
                data['cmd'],
                datetime.strptime(data['datetime'], DATETIME_FORMAT), 
                data['count'],
                data['on_time_vol'],
                data['off_time_vol'],
                data['device']
                )
            
            for time in data['time']:
                cmd.append_data(COnOffTime(time['on_time'], time['off_time']))
            self._db.set_data(cmd)
            
        return None

    ##########################################################################################
    # data 를 file 로 export 할 때 DDS callback 에서 처리하면 그동안 DDS 동작 불가라서
    # data 를 queue 에 넣고 thread 에서 file 로 export
    # return : None
    ##########################################################################################
    #def export_data(self, q):
    #    while self.exit_thread is False:
    #        QtCore.QCoreApplication.processEvents()
    #        while not q.empty():
    #            QtCore.QCoreApplication.processEvents()
    #            value = q.get()
    #            self.export(value)
    #            q.task_done()
    #        time.sleep(1)
    #    return None