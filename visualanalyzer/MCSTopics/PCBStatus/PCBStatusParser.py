# ts.kim : 20231114 : PMD-36-mcs-parser : PCB Status Instance Factory

import sys, os
MCSTopicsPath = os.path.join(os.path.dirname(os.path.abspath(os.path.dirname(__file__))), 'MCSTopics')
sys.path.insert(0, MCSTopicsPath)
PCBStatusPath = os.path.join(MCSTopicsPath, 'PCBStatus')
sys.path.insert(0, PCBStatusPath)

from MCSTopics.PCBStatus.NOT_EXIST_Parser import *
from MCSTopics.PCBStatus.PCB_IN_STATUS_Parser import *
from MCSTopics.PCBStatus.PCB_INCOME_PASSING_Parser import *
from MCSTopics.PCBStatus.PCB_JUST_PASSED_ENTRY_IN_STATUS_Parser import *
from MCSTopics.PCBStatus.PCB_ENTRY_PASSED_INCOME_PASSING_Parser import *
from MCSTopics.PCBStatus.PCB_WORK_STATUS_Parser import *
from MCSTopics.PCBStatus.PCB_WAIT_INSP_DONE_STATUS_Parser import *
from MCSTopics.PCBStatus.PCB_INSP_DONE_STATUS_Parser import *
from MCSTopics.PCBStatus.PCB_OUTLET_PASSING_Parser import *
from MCSTopics.PCBStatus.PCB_OUT_STATUS_Parser import *
from MCSTopics.PCBStatus.PCB_OUT_NEXT_STATUS_Parser import *
from MCSTopics.PCBStatus.PCB_OUT_NEXT_DONE_STATUS_Parser import *
from MCSTopics.PCBStatus.PCB_IN_JAM_Parser import *
from MCSTopics.PCBStatus.PCB_OUT_JAM_Parser import *

import traceback

class PCBStatusParserFactory:
    @staticmethod
    def create_parsers(mcs_pcb_status):
        return [
            CNotExistParser(mcs_pcb_status),
            CPcbEntryPassedIncomePassingParser(mcs_pcb_status),
            CPcbInJamParser(mcs_pcb_status),
            CPcbInStatusParser(mcs_pcb_status),
            CPcbIncomePassingParser(mcs_pcb_status),
            CPcbInspDoneStatusParser(mcs_pcb_status),
            CPcbJustPassedEntryInStatusParser(mcs_pcb_status),
            CPcbOutJamParser(mcs_pcb_status),
            CPcbOutNextDoneStatusParser(mcs_pcb_status),
            CPcbOutNextStatusParser(mcs_pcb_status),
            CPcbOutStatusParser(mcs_pcb_status),
            CPcbOutletPassingParser(mcs_pcb_status),
            CPcbWaitInspDoneStatusParser(mcs_pcb_status),
            CPcbWorkStatusParser(mcs_pcb_status)
        ]

    @staticmethod
    def load_pcb_status(_pcb_status):
        result = True
        msg = ""
        try:        
            data_list = CJasonManager.read_file(_pcb_status.data_file)
            
            # set data to mcs pcb status module
            for data in data_list:
                pcb_status_data = CMcsPcbStatusData(
                    data['domain'],
                    data['topic'],
                    data['cmd'],
                    datetime.strptime(data['datetime'], DATETIME_FORMAT),
                    data['status'],
                    data['state']
                )
                _pcb_status.set_data(pcb_status_data)
        except MyException as ex:
            result = False
            msg = ex
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result is False:
                PRINT_ERR(msg)