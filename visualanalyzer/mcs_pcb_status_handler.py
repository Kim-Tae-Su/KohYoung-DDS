
#!/usr/local/bin/python3
# -*- coding: UTF-8 -*-

import matplotlib.pyplot as plt
from data_type import *
from datetime import datetime
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from libs.debug import *
import copy
from define import *
from db_handler import *
# # 마우스 휠로 확대/축소 동작 가능, Agg 는 안됨
import matplotlib
matplotlib.use('QtAgg')
from figure_canvas import *
import traceback


MCS_PCB_STATUS_START = 0
MCS_PCB_STATUS_END = 1

# lane type 약어
FRONT_LANE_ENTRY_PCB_STATUS = "_F_EN"
FRONT_LANE_WORK_PCB_STATUS = "_F_WK"
FRONT_LANE_EXIT_PCB_STATUS = "_F_EX"
REAR_LANE_ENTRY_PCB_STATUS = "_R_EN"
REAR_LANE_WORK_PCB_STATUS = "_R_WK"
REAR_LANE_EXIT_PCB_STATUS = "_R_EX"


class CMcsPcbStatusData(CDdsDataHeader):
    def __init__(self, domain = 0, topic = "", cmd = "", time: datetime = 0, status = "", state = 0):
        super().__init__(domain, topic, cmd, time)
        self.status = status
        self.state = state
        return None

class CMcsPcbStatus(CDBHandler, CFigureCanvasHandler):
    def __init__(self):
        CFigureCanvasHandler.__init__(self)
        # packet : DDS 로 전송되는 data set(topic, command, parameter...)
        # 수신 packet, show list 로 옮겨진다
        self.recv_packet_buf = {}
        # cmd 별로 그래프 그리기위해 dict 사용
        # {cmd : [topics], cmd : [topics]}
        # ex) {"FrontLane_Entry_PCB_Status" : [...], "FrontLane_Work_PCB_Status" : [...], ...}
        self.all_packet_buf = {}
        # 그래프로 출력할 packet
        self.show_packet_buf = {}
        # error status 구분
        self.error_status: list[str] = list()
        self.target = TARGET_MCS_PCB_STATUS
        self.data_file = "./db/mcs_pcb_status.json"
        self.fig_width_size_inch = 12
        self.fig_height_size_inch = 7
        self.lane_type_map = {FRONT_LANE_ENTRY_PCB_STATUS:"FrontLane_Entry_PCB_Status", FRONT_LANE_WORK_PCB_STATUS:"FrontLane_Work_PCB_Status",
                              FRONT_LANE_EXIT_PCB_STATUS:"FrontLane_Exit_PCB_Status", REAR_LANE_ENTRY_PCB_STATUS:"RearLane_Entry_PCB_Status",
                              REAR_LANE_WORK_PCB_STATUS:"RearLane_Work_PCB_Status", REAR_LANE_EXIT_PCB_STATUS:"RearLane_Exit_PCB_Status"}                
        return None

    ##########################################################################################
    # Add dds packet of pcb status
    # param :
    #   dds packet      dds packet of pcb status
    #   packet_type        packet type
    # return : None
    ##########################################################################################
    def add_packet(self, packet: CMcsPcbStatusData, packet_type):
        result = True
        msg = ""
        try:
            if packet_type == PACKET_RECV:
                if packet.cmd not in self.recv_packet_buf:
                    self.recv_packet_buf[packet.cmd] = [packet]
                else:
                    self.recv_packet_buf[packet.cmd].append(packet)
            elif packet_type == PACKET_ALL:
                if packet.cmd not in self.all_packet_buf:
                    self.all_packet_buf[packet.cmd] = [packet]
                else:
                    self.all_packet_buf[packet.cmd].append(packet)
            elif packet_type == PACKET_SHOW:
                if packet.cmd not in self.show_packet_buf:
                    self.show_packet_buf[packet.cmd] = [packet]
                else:
                    self.show_packet_buf[packet.cmd].append(packet)
            else:
                raise MyException(f'wrong packet type {packet_type}')
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
    # Clear packet buffer
    # param :
    #   packet_type    packet type    
    ##########################################################################################
    def clear_packet_buf(self, packet_type):
        result = True
        msg = ""
        try:
            if packet_type == PACKET_RECV:
                self.recv_packet_buf.clear()
            elif packet_type == PACKET_ALL:
                self.all_packet_buf.clear()
            elif packet_type == PACKET_SHOW:
                self.show_packet_buf.clear()
            else:
                raise MyException(f'wrong packet type {packet_type}')
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
    # status 로 dds packet 의 cmd 찾는다
    # param :
    #   status          status
    # return : 찾으면 cmd, 못찾으면 None
    ##########################################################################################    
    def get_cmd(self, status:str) -> str:
        result = True
        msg = ""
        try:
            cmd = None            
            for key in self.lane_type_map.keys():
                if key in status:
                    cmd = self.lane_type_map[key]
                    break
            return cmd
        except MyException as ex:
            result = False
            msg = ex
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)
                return None
            
    ##########################################################################################    
    # datetime, status 로 packet을 찾는다
    # param :
    #   datetime_obj    datetime
    #   status          status
    # return : 찾으면 packet, 못찾으면 None
    ##########################################################################################    
    def get_packet(self, datetime_obj, status) -> CMcsPcbStatusData:
        result = True
        msg = ""
        try:
            # status 로 command 찾는다
            cmd = self.get_cmd(status)

            if self.all_packet_buf.get(cmd) is not None:                
                for data in self.all_packet_buf[cmd]:
                    if data.datetime == datetime_obj and data.status == status:
                        return data
            else:
                raise MyException(f'{cmd} is not exist')
            raise MyException(f'{cmd} {datetime_obj} {status} is not exist')
        except MyException as ex:
            result = False
            msg = ex
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)
                return None
    
    ##########################################################################################
    # packet list 에서 status 의 state 가 parameter state 인 data 를 return
    #   해당되는 data 가 없으면 return None
    # param : 
    #   topics_per_cmd          cmd 별 topic list
    #   start_index             list 내의 start index
    #   status                  status
    #   state                   찾을 data 의 state
    # return : pcb status data
    ##########################################################################################
    def get_data_by_status_state(self, topics_per_cmd:list[CMcsPcbStatusData], start_index, status, state):
        result = True
        msg = ""
        try:
            topics_len = len(topics_per_cmd)
            for i in range(topics_len):
                if i + start_index >= topics_len:
                    break
                else:
                    if topics_per_cmd[i + start_index].status == status and topics_per_cmd[i + start_index].state == state:
                        return topics_per_cmd[i + start_index]
            return None
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
    # topic 의 state의 start, end 쌍을 맞춘다
    #   start 만 온 경우 end 추가, end 만 온 경우 start 추가
    # ex) data 미수신이던 사용자가 선택을 안했던, show 할 때는 start, end 쌍을 맞춰야
    # 그래프가 표시된다.
    # topic 의 state가 start 만 오고 end 가 없는 경우가 있다.
    # 
    # param :
    #   packets          packets for pcb status, dict type
    ##########################################################################################
    def make_pair_state(self, packets: dict):
        result = True
        msg = ""
        try:
            topics_per_cmd:list[CMcsPcbStatusData]
            for topics_per_cmd in packets.values():
                # topic 별로 end state 없으면 dummy 추가
                for data in topics_per_cmd:
                    if data.state == MCS_PCB_STATUS_START:
                        # state 가 end 인 data 찾는다
                        found_data = self.get_data_by_status_state(topics_per_cmd, 0, data.status, MCS_PCB_STATUS_END)
                        if found_data == None:
                            # state 가 start 만 오고 end 는 안온 경우 예외 처리                    
                            PRINT_ERR(f"not found end data for {data.status}, do exception handle")
                            found_data = copy.deepcopy(data)
                            found_data.state = MCS_PCB_STATUS_END
                            # 기존 packet list 에 dummy 추가
                            topics_per_cmd.append(found_data)
                            self.error_status.append(found_data.status)
                        else:
                            pass
                    elif data.state == MCS_PCB_STATUS_END:
                        # state 가 start 인 data 를 list 처음부터 찾는다
                        found_data = self.get_data_by_status_state(topics_per_cmd, 0, data.status, MCS_PCB_STATUS_START)
                        if found_data == None:
                            # state 가 end 만 오고 start 는 안온 경우 예외 처리                    
                            PRINT_ERR(f"not found start data for {data.status}, do exception handle")
                            found_data = copy.deepcopy(data)
                            found_data.state = MCS_PCB_STATUS_START
                            # 기존 topic list 에 dummy 추가
                            topics_per_cmd.append(found_data)
                            self.error_status.append(found_data.status)
                        else:
                            pass
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
    # packet list 에서 datetime 이 제일 빠른 것 찾기
    #   data 없으면 return None
    # param : 
    #   cmd_list          pcb status data list
    ##########################################################################################
    def get_earliest_time(self, cmd_list: list[CMcsPcbStatusData]):
        time_list = []
        for data in cmd_list:
            time_list.append(data.datetime)
        if len(time_list) > 0:
            return min(time_list)
        return None

    ##########################################################################################
    # Show pcb status
    #   topic 마다 그래프를 그린다
    # param : 
    #   layout              그래프 추가할 layout
    # return : scene 에 다음에 추가할 postion y
    ##########################################################################################
    def show(self, layout):    
        result = True
        msg = ""
        try:
            pcb_status_value_map = {"NOT_EXIST":0, "PCB_IN_STATUS":1, "PCB_INCOME_PASSING":2, "PCB_JUST_PASSED_ENTRY_IN_STATUS":3, "PCB_ENTRY_PASSED_INCOME_PASSING":4,
                               "PCB_WORK_STATUS":5, "PCB_WAIT_INSP_DONE_STATUS":6, "PCB_INSP_DONE_STATUS":7, "PCB_OUTLET_PASSING":8, "PCB_OUT_STATUS":9, "PCB_OUT_NEXT_STATUS":10,
                               "PCB_OUT_NEXT_DONE_STATUS":11, "PCB_IN_JAM":12, "PCB_OUT_JAM":13}
            
            # 기존 error packet 제거
            self.error_status.clear()

            # packet 의 state의 start, end 쌍을 맞춘다
            self.make_pair_state(self.show_packet_buf)
            
            num_topics = len(self.show_packet_buf.keys())
            if num_topics == 0:
                PRINT_INFO(f'num_topics 0')
                return None
            
            # 새로운 fig, ax 에 그래프 그리기
            fig, ax_list_org = plt.subplots(num_topics, 1, figsize=(self.fig_width_size_inch, self.fig_height_size_inch * num_topics), gridspec_kw={'hspace': 0.5})
            ax_list = list()
            if num_topics == 1:
                ax_list.append(ax_list_org)
            elif num_topics > 1:
                for i in range(num_topics):
                    ax_list.append(ax_list_org[i])

            # Create a FigureCanvas for the current figure
            canvas = FigureCanvas(fig)

            # event.key 가 none 으로 나오는 문제 수정
            canvas.setFocusPolicy(QtCore.Qt.ClickFocus)
            canvas.setFocus()

            topics_per_cmd:list[CMcsPcbStatusData]
            for i, topics_per_cmd in enumerate(self.show_packet_buf.values()):
                if len(topics_per_cmd) > 0:
                    first_time = self.get_earliest_time(topics_per_cmd)
                    x_values_start = []
                    x_values_end = []
                    y_values = []

                    for data in topics_per_cmd:
                        time_ms = int((data.datetime - first_time).total_seconds() * 1000)  # ms
                        if data.state == MCS_PCB_STATUS_START:
                            x_values_start.append(time_ms)
                            y_values.append(pcb_status_value_map[data.topic] + 1)
                        else:
                            x_values_end.append(time_ms)
                    
                    # show 할 data 가 있어야 그래프 그리기
                    if len(x_values_start) > 0:
                        # # 새로운 fig, ax 에 그래프 그리기
                        ax_list[i].set_title(data.cmd)
                        ax_list[i].set_xlabel('time(ms)')
                        ax_list[i].set_ylabel('PCB Status')

                        bar_widths = [end - start for start, end in zip(x_values_start, x_values_end)]
                        ax_list[i].barh(y_values, width=bar_widths, left=x_values_start, color='green')

                        x_ticks = [0] + x_values_end
                        ax_list[i].set_xticks(x_ticks)
                        
                        y_labels = ['', 'NOT_EXIST', 'PCB_IN_STATUS', 'PCB_INCOME_PASSING', 'PCB_JUST_PASSED_ENTRY_IN_STATUS', 'PCB_ENTRY_PASSED_INCOME_PASSING', 'PCB_WORK_STATUS', 'PCB_WAIT_INSP_DONE_STATUS', 'PCB_INSP_DONE_STATUS', 'PCB_OUTLET_PASSING', 'PCB_OUT_STATUS', 'PCB_OUT_NEXT_STATUS', 'PCB_OUT_NEXT_DONE_STATUS', 'PCB_IN_JAM', 'PCB_OUT_JAM']
                        ax_list[i].set_yticks(range(len(y_labels)))
                        ax_list[i].set_yticklabels(y_labels, fontdict=text_font)

                        # state 가 start - end 쌍이 아닌 경우 텍스트 색깔 다르게
                        for label in self.error_status:
                            ax_list[i].get_yticklabels()[y_labels.index(label)].set_color('red')

                        fig.subplots_adjust(left=0.3, right=0.9, top=0.9, bottom=0.1)

            canvas.mpl_connect('scroll_event', self.on_scroll)
            canvas.mpl_connect('button_press_event', self.on_button_press)
            canvas.mpl_connect('button_release_event', self.on_button_release)
            canvas.mpl_connect('motion_notify_event', self.on_mouse_motion)

            # view 를 layout 에 추가
            layout.addWidget(canvas)
            return None
        except MyException as ex:
            result = False
            msg = ex
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)