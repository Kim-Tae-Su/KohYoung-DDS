# ts.kim : 20231114 : PMD-36-mcs-parser : Cycle Time Instance Factory

import sys, os
MCSTopicsPath = os.path.join(os.path.dirname(os.path.abspath(os.path.dirname(__file__))), 'MCSTopics')
sys.path.insert(0, MCSTopicsPath)
CycleTimePath = os.path.join(MCSTopicsPath, 'CycleTime')
sys.path.insert(0, CycleTimePath)

from MCSTopics.CycleTime.OPRUN_START_Parser import*
from MCSTopics.CycleTime.OPRUN_END_Parser import*
from MCSTopics.CycleTime.PCB_INSP_START_Parser import*
from MCSTopics.CycleTime.PCB_INSP_END_Parser import*
from MCSTopics.CycleTime.LANE_INSP_START_Parser import*
from MCSTopics.CycleTime.LANE_INSP_END_Parser import*
from MCSTopics.CycleTime.FID_INSP_START_Parser import*
from MCSTopics.CycleTime.FID_INSP_END_Parser import*
from MCSTopics.CycleTime.FOV_INSP_START_Parser import*
from MCSTopics.CycleTime.FOV_INSP_END_Parser import*
from MCSTopics.CycleTime.TRANSFER_TIME_START_Parser import*
from MCSTopics.CycleTime.TRANSFER_TIME_END_Parser import*
from MCSTopics.CycleTime.TURNAROUND_TIME_START_Parser import*
from MCSTopics.CycleTime.TURNAROUND_TIME_END_Parser import*

from MCSTopics.CycleTime.SMEMA_Parser import*
from handle_json import *
from MCSTopics.McsTopicHandler import *
import traceback

class CycleTimeParserFactory:
    @staticmethod
    def create_parsers(mcs_cycle_time):
        return [
            #COprunStartParser(mcs_cycle_time),
            #COprunEndParser(mcs_cycle_time),
            #CPcbInspStartParser(mcs_cycle_time),
            #CPcbInspEndParser(mcs_cycle_time),
            #CLaneInspStartParser(mcs_cycle_time),
            #CLaneInspEndParser(mcs_cycle_time),
            #CFidInspStartParser(mcs_cycle_time),
            CFidInspEndParser(mcs_cycle_time),
            CFovInspStartParser(mcs_cycle_time),
            CFovInspEndParser(mcs_cycle_time),
            #CTurnaroundStartParser(mcs_cycle_time),
            #CTurnaroundEndParser(mcs_cycle_time),
            #CTransferStartParser(mcs_cycle_time),
            #CTransferEndParser(mcs_cycle_time),
            #CSmemaParser(mcs_cycle_time)
        ]

    @staticmethod
    def load_cycle_time(mcs_cycle_time):
        result = True
        msg = ""
        try:        
            data_list = CJasonManager.read_file(mcs_cycle_time.data_file)
            
            # set data to mcs pcb status module
            for data in data_list:
                if 'coordinate' in data:
                    cycle_time_data = CFovMovingTimeData(
                    data['domain'],
                    data['topic'],
                    data['cmd'],
                    datetime.strptime(data['datetime'], DATETIME_FORMAT),
                    data['seq'],
                    data['state'],
                    data['coordinate']
                )
                else:
                    cycle_time_data = CCycleTimeData(
                    data['domain'],
                    data['topic'],
                    data['cmd'],
                    datetime.strptime(data['datetime'], DATETIME_FORMAT),
                    data['seq'],
                    data['state']
                )
                mcs_cycle_time.set_data(cycle_time_data)
        except MyException as ex:
            result = False
            msg = ex
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result is False:
                PRINT_ERR(msg)