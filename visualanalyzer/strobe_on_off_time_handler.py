
#!/usr/local/bin/python3
# -*- coding: UTF-8 -*-


import matplotlib.pyplot as plt
from data_type import *
from datetime import datetime
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from libs.debug import *
from define import *
from db_handler import *
# 마우스 휠로 확대/축소 동작 가능, Agg 는 안됨
import matplotlib
matplotlib.use('QtAgg')
from figure_canvas import *
import traceback


class CStrobeOnOffTimeData(CDdsDataHeader):
    def __init__(self, domain = 0, topic = "", cmd = "", time: datetime = 0, count = 0, on_time_vol = 3, off_time_vol = 0, device: str = "unknown"):
        super().__init__(domain, topic, cmd, time)
        self.count = count
        self.on_time_vol = on_time_vol                  # on time voltage
        self.off_time_vol = off_time_vol                # off time voltage
        self.device = device                            # device name, ex) MPVC, MVC, IVPC
        self.on_off_time: list[COnOffTime] = list()
        return None
    
    ##########################################################################################
    # clear appended data
    # return : None
    ##########################################################################################
    def clear_data(self):
        self.on_off_time.clear()
        return None

    ##########################################################################################
    # append data
    # return : None
    ##########################################################################################
    def append_data(self, data : COnOffTime):
        self.on_off_time.append(data)
        return None

    ##########################################################################################
    # Set strobe on off time count
    #   on time, off time 한 쌍이 1개
    # param :
    #   count   : on off time count
    # return : None
    ##########################################################################################
    def set_count(self, count:int):
        self.count = count
        return None

    ##########################################################################################
    # Set on time, off time voltage
    # param :
    #   on_time_vol   : on time voltage
    #   off_time_vol  : off time voltage
    # return : None
    ##########################################################################################
    def set_voltage(self, on_time_vol:int, off_time_vol:int):
        self.on_time_vol = on_time_vol
        self.off_time_vol = off_time_vol
        return None
    
    ##########################################################################################
    # Set device name
    # param :
    #   device   : device name
    # return : None
    ##########################################################################################
    def set_device(self, device:str):
        self.device = device
        return None
        
    ##########################################################################################
    # Set datetime
    # param :
    #   time   : datetime
    # return : None
    ##########################################################################################
    def set_datetime(self, time:datetime):
        self.datetime = time
        return None

class CStrobeOnOffTime(CDBHandler, CFigureCanvasHandler):
    def __init__(self):
        CFigureCanvasHandler.__init__(self)
        # 수신 packet buffer, show 할 때 삭제된다
        self.recv_packet_buf : list[CStrobeOnOffTimeData] = list()
        # 모든 수신 packet buffer
        self.all_packet_buf : list[CStrobeOnOffTimeData] = list()
        # 그래프로 출력할 packet buffer
        self.show_packet_buf: list[CStrobeOnOffTimeData] = list()
        self.target = TARGET_STROBE_ON_OFF_TIME
        self.data_file = "./db/strobe_on_off_time.json"
        self.fig_width_size_inch = 14
        self.fig_height_size_inch = 4
        return None

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
    # Add packet of strobe on off time
    # param :
    #   packet         packet of strobe on off time
    #   packet_type    packet type    
    # return : None
    ##########################################################################################
    def add_packet(self, packet: CStrobeOnOffTimeData, packet_type):
        result = True
        msg = ""
        try:
            if packet_type == PACKET_RECV:
                self.recv_packet_buf.append(packet)
            elif packet_type == PACKET_ALL:
                self.all_packet_buf.append(packet)
            elif packet_type == PACKET_SHOW:
                self.show_packet_buf.append(packet)
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
    # datetime 과 device로 packet 를 찾는다
    # param :
    #   datetime_obj    datetime
    #   device          vpc device name
    # return : 찾으면 packet, 못찾으면 None
    ##########################################################################################    
    def get_packet(self, datetime_obj, device) -> CStrobeOnOffTimeData:
        result = True
        msg = ""
        try:
            for packet in self.all_packet_buf:
                if packet.device == device and packet.datetime == datetime_obj:
                    return packet
            raise MyException(f'{datetime_obj} {device} {datetime_obj} is not exist')
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
    # Show strobe on off time with graph
    # param : 
    #   layout              그래프 추가할 layout
    # return : scene 에 다음에 추가할 postion y
    ##########################################################################################
    def show(self, layout:QVBoxLayout):
        result = True
        msg = ""
        try:
            num_devices = len(self.show_packet_buf)
            if num_devices == 0:
                PRINT_INFO(f'num_devices 0')
                return None
            
            # 새로운 fig, ax 에 그래프 그리기
            fig, ax_list_org = plt.subplots(num_devices, 1, figsize=(self.fig_width_size_inch, self.fig_height_size_inch * num_devices), gridspec_kw={'hspace': 0.4})
            ax_list = list()
            if num_devices == 1:
                ax_list.append(ax_list_org)
            elif num_devices > 1:
                for i in range(num_devices):
                    ax_list.append(ax_list_org[i])

            # Create a FigureCanvas for the current figure
            canvas = FigureCanvas(fig)

            # event.key 가 none 으로 나오는 문제 수정
            canvas.setFocusPolicy(QtCore.Qt.ClickFocus)
            canvas.setFocus()

            for k in range(num_devices):
                ax_list[k].set_title(self.show_packet_buf[k].device + ' strobe on off time')
                ax_list[k].set_xlabel("Time(us)")
                ax_list[k].set_ylabel("Voltage")

                old_time = 0

                for i in range(len(self.show_packet_buf[k].on_off_time)):
                    # Plot the on time
                    # hlines(y, xmin, xmax)
                    ax_list[k].hlines(self.show_packet_buf[k].on_time_vol, old_time, old_time + self.show_packet_buf[k].on_off_time[i].on_time , color='red', linestyle='solid', linewidth=1)
                    # vlines(x, ymin, ymax)
                    ax_list[k].vlines(old_time + self.show_packet_buf[k].on_off_time[i].on_time, self.show_packet_buf[k].off_time_vol, self.show_packet_buf[k].on_time_vol, color='red', linestyle='solid', linewidth=1)
                    old_time += self.show_packet_buf[k].on_off_time[i].on_time

                    # Plot the off self.show_packet_buf[k]
                    ax_list[k].hlines(self.show_packet_buf[k].off_time_vol, old_time, old_time + self.show_packet_buf[k].on_off_time[i].off_time , color='red', linestyle='solid', linewidth=1)
                    ax_list[k].vlines(old_time + self.show_packet_buf[k].on_off_time[i].off_time, self.show_packet_buf[k].off_time_vol, self.show_packet_buf[k].on_time_vol, color='red', linestyle='solid', linewidth=1)
                    old_time += self.show_packet_buf[k].on_off_time[i].off_time

            canvas.mpl_connect('scroll_event', self.on_scroll)
            canvas.mpl_connect('button_press_event', self.on_button_press)
            canvas.mpl_connect('button_release_event', self.on_button_release)
            canvas.mpl_connect('motion_notify_event', self.on_mouse_motion)

            # 여러 axes 그릴 때 margin 조정
            subplots_adjust_top = 0.9 + 0.01 * num_devices
            subplots_adjust_bottom = 0.13 - 0.01 * num_devices
            fig.subplots_adjust(left=0.1, right=0.9, top=subplots_adjust_top, bottom=subplots_adjust_bottom)

            layout.addWidget(canvas)
            return None
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)