
#!/usr/local/bin/python3
# -*- coding: UTF-8 -*-


# import sys
from data_type import *
from strobe_on_off_time_handler import *
from handle_json import *
from KYITopics import *
from KYITopics.strobe_on_off_time_data_handler import *
from mcs_pcb_status_handler import *
from mcs_cycle_time_handler import *

from MCSTopics.PCBStatus.PCBStatusParser import PCBStatusParserFactory
from MCSTopics.CycleTime.CycleTimeParser import CycleTimeParserFactory
from mcs_machine_learning import *

import threading
import time
from libs.debug import *
from DdsHeader import *

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QGraphicsView, QGraphicsScene
from main_win import Ui_MainWindow
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from draw import *
import pyuac
from figure_canvas import *

# plt.subplots 실행 시 윈도우 생성 안하기
import matplotlib
matplotlib.use('Agg')
from figure_canvas import *

# KYI data 처리
from kyi_handler import *
from KYITopics.grab_start_parser import *
from KYITopics.grab_end_parser import *
from KYITopics.grabber_start_parser import *
from KYITopics.grabber_end_parser import *
from KYITopics.grabber_command_start_parser import *
from KYITopics.grabber_command_end_parser import *
from KYITopics.grabber_reinit_start_parser import *
from KYITopics.grabber_reinit_end_parser import *
from KYITopics.grab_done_start_parser import *
from KYITopics.grab_done_end_parser import *
import traceback
from typing import Optional


VA_VER = '0.1'


DATETIME_FORMAT = "%Y-%m-%d_%H:%M:%S.%f"
FIG_WIDTH_INCH_PER_MS = 0.1
FIG_WIDTH_INCH_MIN = 14
FIG_HEIGHT_INCH_PER_AXES = 2
FIG_HEIGHT_INCH_MIN = 7

# tab 구분
TAB_DEFAULT_GRAPH = 0
TAB_SQUARE_WAVE = 1
TAB_DATA_ANALYSIS1=2
TAB_DATA_ANALYSIS2=3

# real time view 에서 몇초마다 그래프를 update 할지
REAL_TIME_SLEEP_SEC = 1

REAL_TIME_VIEW_DATA_MAX_COUNT = 100
MAX_FIG_PIX_COUNT = 65535

# square wave 는 20초 동안을 보여준다
SQAURE_WAVE_MAX_DURATION_SEC = 20


class WorkerThread(QThread):
    update_signal = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.event_run = threading.Event()
        self.exit_thread = False

    def run(self):
        while not self.exit_thread:
            self.event_run.wait()
            self.event_run.clear()        # event clear 안하면 event 는 계속 set 상태 유지
            self.update_signal.emit()
            time.sleep(REAL_TIME_SLEEP_SEC)

    def run_work(self):
        self.event_run.set()

    def stop_work(self):
        self.event_run.clear()
    
    # 객체 삭제 전 객체 내 thread 먼저 종료해야한다
    def finalize(self):
        # thread loop 종료시키기
        self.exit_thread = True 


class CVisualAnalyzer(QMainWindow, Ui_MainWindow, CFigureCanvasHandler, CPrintThread):
    # 객체 선언, .누르면 method 보이기 위함
    centralwidget:QtWidgets.QWidget
    output:QtWidgets.QListWidget
    
    def __init__(self) -> None:
        self.result_layout: list[QLayout] = list()
        
        # Show UI
        super().__init__()
        self.setupUi(self)
        self.init_ui()

        CPrintThread.__init__(self)

        CFigureCanvasHandler.__init__(self)

        self.strobe_on_off_time = CStrobeOnOffTime()
        self.strobe_on_off_time_data_h = CStrobeOnOffTimeDataHandler(self.strobe_on_off_time)
        
        self.mcs_machine_learning=CMcsMachineLearning()
        self.mcs_machine_learning.feature_engineer()
        self.mcs_machine_learning.LinearRegressionModel()
        self.mcs_machine_learning.PolynomialRidgeModel()
        self.mcs_machine_learning.treeModel()
        
        self.mcs_pcb_status = CMcsPcbStatus()
        self.mcs_cycle_time = CMcsCycleTime(self.mcs_machine_learning)

        # ts.kim 231101 : Create parsers using the factory method
        #self.pcb_status_parsers = PCBStatusParserFactory.create_parsers(self.mcs_pcb_status)
        self.pcb_status_parsers=[]
        self.cycle_time_parsers = CycleTimeParserFactory.create_parsers(self.mcs_cycle_time)
        # self.pcb_status_parsers = []    # test
        # self.cycle_time_parsers = []
 
        # KYI data(topic) 처리
        self.kyi = CKyi()       # KYI data(topic) 처리 handler
        #self.kyi_parsers = [CGrabStartParser(self.kyi), CGrabEndParser(self.kyi), CGrabberStartParser(self.kyi), CGrabberEndParser(self.kyi),
        #                    CGrabberCommandStartParser(self.kyi), CGrabberCommandEndParser(self.kyi), CGrabberReinitStartParser(self.kyi), CGrabberReinitEndParser(self.kyi),
        #                    CGrabDoneStartParser(self.kyi), CGrabDoneEndParser(self.kyi)]
        self.kyi_parsers =[]

        self.check_thread = threading.Thread(target=self.check_data_recv)
        self.exit = False                   # thread loop 종료시키기
        self.fig_over_size = False          # figure 의 width 와 height 는 65535 이하여야한다. 넘을 때 True
        self.draw = CDraw()                 # real time view 에서 dummy 추가위해 member 로 이동

        self.worker_thread = WorkerThread()
        self.worker_thread.update_signal.connect(self.show_real_time_view)
        self.worker_thread.start()  # run() 호출

        self.playing = False                # real time view
        self.showInfo = False               # annotat 보여줄지 여부
        self.fig = None
        # 실시간 그래프 출력하다 멈춘 후 event 처리하기 위해 마지막 canvas 필요하다
        self.canvas = None
        self.real_time_drawing = False                 # draw 중인지 여부
        self.init()

    ##########################################################################################
    # close event 처리
    ##########################################################################################
    def closeEvent(self, QCloseEvent):
        # thread loop 종료시키기
        self.exit = True
        # thread 종료 대기
        self.check_thread.join()
        # 현재 widget instance 삭제
        self.deleteLater()
        QCloseEvent.accept()

        # 객체 삭제 전 객체 내 thread 먼저 종료해야한다
        self.strobe_on_off_time_data_h.finalize()
        for parser in self.pcb_status_parsers:
            parser.finalize()
        for parser in self.cycle_time_parsers:
            parser.finalize()
        
        for parser in self.kyi_parsers:
            parser.finalize()

        self.worker_thread.finalize()

    def __del__(self):
        pass

    ##########################################################################################
    # 그래프 표시되는 Result window 초기화
    ##########################################################################################
    def init_result_win(self):
        result = True
        msg = ""
        try:        
            # subwindow 를 mdi 에 추가
            self.win_result = QMdiSubWindow()
            self.win_result.setWindowTitle("Result")
            self.mdi.addSubWindow(self.win_result)

            #### 출력 그래프 별 Tab 추가
            self.tab_result_widget = QTabWidget()

            # 기본 요구사항 그래프
            self.default_graph = QScrollArea()
            # scroll bar 에 대해 eventFilter 설치
            self.default_graph.verticalScrollBar().installEventFilter(self)         

            # Square wave chart
            self.square_wave = QScrollArea()
            # scroll bar 에 대해 eventFilter 설치
            self.square_wave.verticalScrollBar().installEventFilter(self)       
            
            # Machine Learning Data Analysis Graph
            self.data_analysis_graph1 = QScrollArea()
            # scroll bar 에 대해 eventFilter 설치
            self.data_analysis_graph1.verticalScrollBar().installEventFilter(self)   
            # Machine Learning Data Analysis Graph
            self.data_analysis_graph2 = QScrollArea()
            # scroll bar 에 대해 eventFilter 설치
            self.data_analysis_graph2.verticalScrollBar().installEventFilter(self)   

            self.tab_result_widget.addTab(self.default_graph, "Default Graph")
            self.tab_result_widget.addTab(self.square_wave, "Square wave chart")
            # ts.kim : 240122 : Machine Learning Data Analysis
            self.tab_result_widget.addTab(self.data_analysis_graph1, "Data analysis graph1")
            self.tab_result_widget.addTab(self.data_analysis_graph2, "Data analysis graph2")


            # 초기 선택 탭을 두 번째 탭으로 설정
            self.tab_result_widget.setCurrentIndex(1)            
            
            ### 툴바 생성 및 액션 추가            
            toolbar = QToolBar()
            # resize full
            icon = QIcon(":/icon/resize_full.png")
            self.actionResizeFull = QAction(icon, "actionResizeFull", self)
            self.actionResizeFull.setCheckable(True)
            toolbar.addAction(self.actionResizeFull)
            self.actionResizeFull.toggled['bool'].connect(self.resize_full)

            # play
            icon = QIcon(":/icon/play.png")
            self.actionPlay = QAction(icon, "actionPlay", self)
            self.actionPlay.setCheckable(True)
            toolbar.addAction(self.actionPlay)
            self.actionPlay.triggered.connect(self.play)

            # pause
            icon = QIcon(":/icon/pause.png")
            self.actionPause = QAction(icon, "actionPause", self)
            toolbar.addAction(self.actionPause)
            self.actionPause.triggered.connect(self.pause)

            # info
            icon = QIcon(":/icon/info.png")
            self.actionInfo = QAction(icon, "actionInfo", self)
            self.actionInfo.setCheckable(True)
            toolbar.addAction(self.actionInfo)
            self.actionInfo.triggered.connect(self.show_info)
            ################################

            layout = QVBoxLayout()
            layout.addWidget(toolbar)
            layout.addWidget(self.tab_result_widget)

            central_widget = QWidget()
            central_widget.setLayout(layout)
            self.win_result.setWidget(central_widget)            
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)

    ##########################################################################################
    # 그래프 표시되는 Result window 초기화
    ##########################################################################################    
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel and event.modifiers() & Qt.ControlModifier:
            # control + 마우스휠 에 대해 scroll bar 움직이지 않게 한다.
            return True
        return super().eventFilter(obj, event)
    
    ##########################################################################################
    # Initialize cmd layout
    ##########################################################################################
    def init_cmd_layout(self):
        self.cmd_layout = QVBoxLayout()
        
        # show button
        self.btn_show = QPushButton('Show', self)
        self.btn_show.clicked.connect(self.click_btn_show)
        
        # clear button
        self.btn_clear = QPushButton('Clear', self)
        self.btn_clear.clicked.connect(self.click_btn_clear)
                
        # cmd tree widget
        self.cmd_tree_widget = MyTreeWidget(self)
        # self.cmd_tree_widget.setAutoScroll(0)     # role ?
        self.cmd_tree_widget.setColumnCount(3)
        self.cmd_tree_widget.setHeaderLabels(["Time", "Name", "Data"])
        self.cmd_tree_widget.setSelectionMode(QTreeWidget.MultiSelection)
        self.cmd_tree_widget.setMinimumWidth(350)
        
        # add widget to layout
        self.cmd_layout.addWidget(self.btn_show)
        self.cmd_layout.addWidget(self.btn_clear)
        self.cmd_layout.addWidget(self.cmd_tree_widget)

    ##########################################################################################
    # 처리할 data 에 해당하는 module return, 없으면 None
    # param :
    #   data      처리할 data
    ##########################################################################################
    def get_module(self, data):
        result = True
        msg = ""
        try:        
            module = None
            if data in STROBE_TIME_DATA_LIST:
                module = self.strobe_on_off_time
            elif data in MCS_CT_DATA_LIST:
                module = self.mcs_cycle_time
            elif data in MCS_PCB_STATUS_DATA_LIST:
                module = self.mcs_pcb_status
            elif data in KYI_DATA_LIST:
                module = self.kyi
            return module
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
    # layout 에 있는 모든 widget 제거
    ########################################################################################## 
    def clear_layout(self, layout:QVBoxLayout):
        if layout:
            while layout.count():
                layout_item = layout.takeAt(0)
                widget = layout_item.widget()
                if widget:
                    widget.deleteLater()

    ##########################################################################################
    # Show 버튼 클릭 시 실행
    #   선택된 packet 들로 그래프 그린다
    ##########################################################################################    
    def click_btn_show(self):
        result = True
        msg = ""
        try:
            # 기존 data clear
            # 안그러면 기존에 선택했다가 현재 선택하지 않은 것도 출력된다
            # TODO list 처리? module_list = [self.strobe_on_off_time, self.mcs_pcb_status, self.mcs_cycle_time]
            self.strobe_on_off_time.clear_packet_buf(PACKET_SHOW)
            self.mcs_pcb_status.clear_packet_buf(PACKET_SHOW)
            self.mcs_cycle_time.clear_packet_buf(PACKET_SHOW)
            self.kyi.clear_packet_buf(PACKET_SHOW)

            # 기존에 추가된 canvas 지우기
            self.clear_layout(self.result_layout[TAB_DEFAULT_GRAPH])
            self.clear_layout(self.result_layout[TAB_SQUARE_WAVE])
            self.clear_layout(self.result_layout[TAB_DATA_ANALYSIS1])
            self.clear_layout(self.result_layout[TAB_DATA_ANALYSIS2])
           

            # 만약 탭 위젯에 이미 레이아웃이 있다면 삭제
            if self.default_graph.layout():
                self.clear_layout(self.default_graph.layout())

            # plt.clf()   # Clear the previous graph before plotting a new one
            
            ############ 선택된 packet 들을 그래프 출력용 data 에 추가
            # tree widget 에서 선택된 dds packet을 해당 module 의 show packet buffer 에 추가
            selected_items = self.cmd_tree_widget.selectedItems()
            for selected_item in selected_items:                
                datetime_text = selected_item.text(COLUMN_TIME).split()
                date_part = datetime_text[0]
                time_part = datetime_text[1]

                # ts.kim : 240131 : 0.000000초일때 0초로 바뀌는 에러 처리
                if '.' not in time_part:
                    time_part += '.000000'

                name = selected_item.text(COLUMN_NAME)
                data = selected_item.text(COLUMN_DATA)
                
                target_module = self.get_module(name)

                # 날짜와 시간 정보를 결합하여 datetime 객체 생성
                datetime_obj = datetime.strptime(f"{date_part}_{time_part}", DATETIME_FORMAT)

                if target_module.target == TARGET_STROBE_ON_OFF_TIME:
                    # datetime, data(vpc, ex] MVC,MVPC,IVPC)로 선택된 packet 을 찾는다
                    found_packet = target_module.get_packet(datetime_obj, data)
                # elif target_module.target == TARGET_MCS_PCB_STATUS or target_module.target == TARGET_MCS_CYCLE_TIME:
                else:
                    # datetime, name 으로 선택된 packet 을 찾는다
                    found_packet = target_module.get_packet(datetime_obj, name)

                if found_packet:
                    target_module.add_packet(found_packet, PACKET_SHOW)
                else:
                    raise MyException(f'not found data with {datetime_obj} {name} {data}')

            # default graph 처리
            if self.strobe_on_off_time.is_buffer_empty(PACKET_SHOW) > 0:                
                self.strobe_on_off_time.show(self.result_layout[TAB_DEFAULT_GRAPH])
            if self.mcs_pcb_status.is_buffer_empty(PACKET_SHOW) > 0:
                self.mcs_pcb_status.show(self.result_layout[TAB_DEFAULT_GRAPH])
            if self.mcs_cycle_time.is_buffer_empty(PACKET_SHOW) > 0:
                self.mcs_cycle_time.show(self.result_layout[TAB_DEFAULT_GRAPH])
            
            # square wave 처리
            # ValueError: Image size of 97000x700 pixels is too large. It must be less than 2^16 in each direction.
            # image width, height 가 각각 65535를 넘을 수 없다
            # 넘게되면 강제로 resize_full 을 enable 시켜서 size 조정한다
            # plot 을 매번 close 후 새로 생성하지 않고 기존 plot 사용하여 성능 개선
            self.draw_square_wave(self.result_layout[TAB_SQUARE_WAVE], self.fig, self.playing)
			               
            if self.playing == False:
                self.set_fig_event(self.fig.axes[0], self.canvas)

            # strobe on off time 안나오는 문제 수정
            if self.fig is not None:
                if int(self.fig.get_figwidth() * self.fig.dpi) >= MAX_FIG_PIX_COUNT or int(self.fig.get_figheight() * self.fig.dpi) >= MAX_FIG_PIX_COUNT:
                    self.fig_over_size = True
                    self.actionResizeFull.setChecked(True)
                    # PRINT_DEBUG(f'fig_over_size {self.fig_over_size}, fig {int(self.fig.get_figwidth() * self.fig.dpi)}x{int(self.fig.get_figheight() * self.fig.dpi)} pixels')
                else:
                    self.fig_over_size = False
                self.fig.set_facecolor('black')  # figure 배경색                

            # resize_full icon 눌렸는지 여부
            is_checked = self.actionResizeFull.isChecked()

            if self.playing == False:
                self.show_result(self.default_graph, self.result_layout[TAB_DEFAULT_GRAPH], is_checked)

            # 실시간 그래프 개선
            # 매번 self.square_wave 에 self.result_layout[TAB_SQUARE_WAVE] 를 setWidget 하면 느리다
            # self.show_result(self.square_wave, self.result_layout[TAB_SQUARE_WAVE], is_checked)

            self.default_graph.setFocusPolicy(QtCore.Qt.ClickFocus)
            self.default_graph.setFocus()          
            
            if self.mcs_cycle_time.is_buffer_empty(PACKET_SHOW) > 0:
                self.mcs_cycle_time.show_analysis1(self.result_layout[TAB_DATA_ANALYSIS1])
                self.mcs_cycle_time.show_analysis2(self.result_layout[TAB_DATA_ANALYSIS2])

            if self.playing == False:
                self.show_result(self.data_analysis_graph1, self.result_layout[TAB_DATA_ANALYSIS1], is_checked)
                self.show_result(self.data_analysis_graph2, self.result_layout[TAB_DATA_ANALYSIS2], is_checked)

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
    # 수신된 data 의 결과 출력
    # param :
    #   target          결과를 출력할 tab
    #   layout          결과를 가지고있는 layout
    #   resize_full     그래프를 window 에 꽉차게 표현 여부
    ##########################################################################################
    def show_result(self, target:QScrollArea, layout:QLayout, resize_full = False):
        result = True
        msg = ""
        try:
            result_widget = QWidget()
            result_widget.setLayout(layout)
            if resize_full == True or self.fig_over_size == True:
                # resize full 에서 height 는 layout 의 height 를 유지한다.
                # tab height 로 맞추면 3번째 그래프부터 짤리는 경우가 있다.
                # 단, real time view 에서 height는 꽉찬 화면으로 고정
                if self.playing:
                    height = self.tab_result_widget.height() - 35
                else:
                    height = layout.sizeHint().height()
                result_widget.setGeometry(0, 0, self.tab_result_widget.width() - 10, height)
            target.setWidget(result_widget) # emit 느려
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)
        return None
    
    ##########################################################################################
    # 그래프 그리는 start, end 시간에 따라 figure width 를 동적으로 정한다
    #   1ms 당 약 0.27 inch
    #   ex) 그래프 그리는 start, end 시간이 길수록 figure width 가 길어야 그래프 표현이 용이
    # param :
    #   duration    그래프 그리는 end - start 의 datetime
    #   fig_dpi     fig 의 1인치 당 pixel 수
    ##########################################################################################
    def get_fig_width(self, duration:datetime, fig_dpi):
        time_ms = int(duration.total_seconds() * 1000)  # ms
        fig_width_inch = time_ms * FIG_WIDTH_INCH_PER_MS
        fig_width_inch = max(fig_width_inch, FIG_WIDTH_INCH_MIN)
        # pixel count 가 65535(MAX_FIG_PIX_COUNT) 를 초과하면 안된다
        max_inch = MAX_FIG_PIX_COUNT / fig_dpi
        fig_width_inch = min(fig_width_inch, max_inch)
        # PRINT_DEBUG(f'duration : {time_ms}, width : {fig_width_inch}')
        return fig_width_inch
    
    ##########################################################################################
    # 그릴 그래프(axes) 개수에 따라 fig height 를 동적으로 정한다
    # param :
    #   axes_count    그릴 그래프 개수
    #   fig_dpi     fig 의 1인치 당 pixel 수    
    ##########################################################################################
    def get_fig_height(self, axes_count, fig_dpi):
        fig_height_inch = axes_count * FIG_HEIGHT_INCH_PER_AXES
        fig_height_inch = max(fig_height_inch, FIG_HEIGHT_INCH_MIN)
        # pixel count 가 65535(MAX_FIG_PIX_COUNT) 를 초과하면 안된다
        max_inch = MAX_FIG_PIX_COUNT / fig_dpi
        fig_height_inch = min(fig_height_inch, max_inch)        
        # PRINT_DEBUG(f'axes_count : {axes_count}, height : {fig_height_inch}')
        return fig_height_inch

    ##########################################################################################
    # square wave data 개수 제한
    #   과거 data 를 제거하여 개수를 제한한다.
    # param :
    #   keep_count        제한할 data 개수
    ##########################################################################################
    def keep_square_wave_data_count(self, keep_count):
        result = True
        msg = ""
        try:
            key_list = list(self.draw.square_wave_data.keys())
            for key in key_list:
                count = len(self.draw.square_wave_data[key])
                del_count = count - keep_count
                if del_count > 0:
                    del self.draw.square_wave_data[key][0:del_count]     # 0번째부터 del_count -1 번째까지 삭제
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
    # Draw square wave
    # param :
    #   layout              결과를 출력할 layout
    #   is_real_time        real time 으로 그릴지 여부
    ##########################################################################################    
    def draw_square_wave(self, layout:QLayout, fig: Optional[plt.Figure] = None, is_real_time:bool = False):
        result = True
        msg = ""
        try:
            # plt.close('all')
            if is_real_time:
                target_buf_type = PACKET_RECV
            else:
                target_buf_type = PACKET_SHOW

            # make datetime list
            for data in self.mcs_cycle_time.get_buffer(target_buf_type):
                data:CCycleTimeData
                if data.state == 0:  # start
                    level = self.draw.VOL_MAX
                else:
                    level = self.draw.VOL_MIN
                self.draw.add_square_wave_data(data.topic, data.datetime, level, data.seq)

            for key in self.mcs_pcb_status.get_buffer(target_buf_type).keys():
                for data in self.mcs_pcb_status.get_buffer(target_buf_type)[key]:
                    data:CMcsPcbStatusData
                    if data.state == 0:  # start
                        level = self.draw.VOL_MAX
                    else:
                        level = self.draw.VOL_MIN                    
                    self.draw.add_square_wave_data(data.topic, data.datetime, level, data.cmd)
            
            # KYI data 처리
            for data in self.kyi.get_buffer(target_buf_type):
                data:CDdsDataHeader
                temp_name = data.topic.replace('Start', '')
                temp_name = temp_name.replace('End', '')
                if "Start" in data.topic:  # start
                    level = self.draw.VOL_MAX
                else:
                    level = self.draw.VOL_MIN
                self.draw.add_square_wave_data(data.topic, data.datetime, level, temp_name)

            if len(self.draw.square_wave_data.keys()) == 0:
                PRINT_INFO(f'data is empty')
                return None, None
            
            if is_real_time:
                # 신규로 수신된 data 없으면 최근 파형 상태(Low, High) 유지위해 dummy data 추가
                new_data_count = len(self.mcs_cycle_time.get_buffer(target_buf_type)) + len(self.mcs_pcb_status.get_buffer(target_buf_type).keys()) + len(self.kyi.get_buffer(target_buf_type))
                if new_data_count == 0:
                    self.draw.add_dummy()
                else:
                    self.draw.align_square_wave_data()

                self.mcs_cycle_time.clear_packet_buf(PACKET_RECV)
                self.mcs_pcb_status.clear_packet_buf(PACKET_RECV)
                self.kyi.clear_packet_buf(PACKET_RECV)

                # real time 일 때 메모리 증가 문제 수정
                self.mcs_cycle_time.clear_packet_buf(PACKET_ALL)
                self.mcs_pcb_status.clear_packet_buf(PACKET_ALL)
                self.kyi.clear_packet_buf(PACKET_ALL)

                if len(self.draw.square_wave_data) == 0:
                    return None, None
             
                # min, max date time
                min_data = CSquareWaveData()
                max_data = CSquareWaveData()
                max_data.datetime = self.draw.get_max_datetime(self.draw.square_wave_data)
                min_data.datetime = max_data.datetime - timedelta(seconds=SQAURE_WAVE_MAX_DURATION_SEC)
            else:
                # dummy min, max 추가
                min_data, max_data = self.draw.add_dummy_min_max()

            if is_real_time:
                # 실시간 경우 square wave data 총 개수 제한
                # dummy 가 계속 추가되기 때문에 성능 하락
                self.keep_square_wave_data_count(REAL_TIME_VIEW_DATA_MAX_COUNT)
    
            square_wave_key_list = list(self.draw.square_wave_data.keys())
            square_wave_count = len(square_wave_key_list)

            if self.fig is None:
                # Create a new figure and axis only if 'fig' is not provided
                self.fig, ax = plt.subplots()
            
            if self.canvas is not None:
                del self.canvas
                self.canvas = None

            if self.canvas == None:
                # Create a FigureCanvas for the current figure
                # self.clear_layout(self.result_layout[TAB_SQUARE_WAVE]) 에서 self.canvas 삭제되어 매번 생성이 필요하다
                self.canvas = FigureCanvas(self.fig)      # real time veiw 시 메모리 증가 원인

            # 모든 서브플롯의 x축 범위를 동일하게 설정
            self.fig.axes[0].set_xlim(min_data.datetime, max_data.datetime)

            # PMD-41 topic 을 datetime 기준으로 오름차순 정렬
            # ex) KYI 에서는 GrabStart, GrabEnd 순으로 보냈지만 VA DDS topic 수신 모듈의 실행 순서에 따라 GrabEnd, GrabStart 순으로 올 때가 있다.
            #     이를 GrabStart, GrabEnd 순으로(datetime) 정렬한다.
            self.draw.order_square_wave_data()

            self.draw.draw_square_wave(self.fig.axes[0], '', self.showInfo)     # memory leak

            self.fig.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.3)
            self.fig.set_size_inches(self.get_fig_width(max_data.datetime - min_data.datetime, self.fig.dpi), self.get_fig_height(square_wave_count, self.fig.dpi))
            layout.addWidget(self.canvas)        # memory leak

            # data 삭제 시점 추후 변경 가능
            if is_real_time == False:
                self.draw.clear()
            return None, None
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
    # figure 에 대한 event(click, scroll, ...) 세팅
    ##########################################################################################    
    def set_fig_event(self, ax, canvas):
        result = True
        msg = ""
        try:
            # event.key 가 none 으로 나오는 문제 수정
            canvas.setFocusPolicy(QtCore.Qt.ClickFocus)
            canvas.setFocus()

            ax_list = list()
            ax_list.append(ax)

            # TODO event 오동작 디버깅
            canvas.mpl_connect('button_press_event', lambda event: self.on_button_press(event, ax_list, self.draw.square_wave_lines))
            canvas.mpl_connect('button_release_event', lambda event: self.on_button_release(event, ax_list, self.draw.square_wave_lines))     
            canvas.mpl_connect('scroll_event', self.on_scroll)
            canvas.mpl_connect('motion_notify_event', lambda event: self.on_mouse_motion(event, self.draw.square_wave_lines))
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)

    ##########################################################################################
    # Clear 버튼 클릭 시 실행
    #   tree widget item 삭제
    #   show cms 삭제
    ##########################################################################################    
    def click_btn_clear(self):
        result = True
        msg = ""
        try:
            self.cmd_tree_widget.clear()
            
            self.strobe_on_off_time.clear_packet_buf(PACKET_SHOW)
            self.mcs_pcb_status.clear_packet_buf(PACKET_SHOW)
            self.mcs_cycle_time.clear_packet_buf(PACKET_SHOW)

            # square wave data 제거
            self.draw.clear()
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
    # UI 초기화 처리
    ##########################################################################################
    def init_ui(self):
        result = True
        msg = ""
        try:
            # window title
            self.setWindowTitle('Visual Analyzer Ver ' + VA_VER)
            
            # window pos
            self.setGeometry(100,50,1500,1000)        
            
            # 메인 윈도우 사이즈 변경 시 내부 위젯들 자동으로 사이즈 조정되기 위해
            # self.centralwidget.setLayout(self.items_layout)
            
            self.mdi = QMdiArea()
            self.setCentralWidget(self.mdi)
            
            # init item layout
            self.init_cmd_layout()
            
            # 수신된 dds packet을 tree widget 으로 표시
            self.cmd_widget = QWidget()
            self.cmd_widget.setLayout(self.cmd_layout)
            
            # packet dockWidget
            self.dock_cmd = QDockWidget("Command", self)
            self.dock_cmd.setWidget(self.cmd_widget)
            # self.dock_cmd.setMinimumSize(300,600)
            self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.dock_cmd)
            self.dock_cmd.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
                        
            self.init_result_win()

            # 각 tab 에 출력할 layout 초기화
            for i in range(len(self.tab_result_widget)):
                self.result_layout.append(QVBoxLayout())
            # self.default_graph.setLayout(self.result_layout[TAB_DEFAULT_GRAPH])
            # 실시간 그래프 개선
            self.square_wave.setLayout(self.result_layout[TAB_SQUARE_WAVE])

            # self.mdi.cascadeSubWindows()
            self.mdi.tileSubWindows()

            # output dockWidget
            self.dock_output = QDockWidget("Output", self)
            self.dock_output.setWidget(self.output)
            self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.dock_output)          
            self.dock_output.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)                      
            
            self.output.clear()
            # debug msg 를 output widget 에 출력하기 위해 handle 세팅
            SetOutputHandle(self.output)
            
            # # data 있는 경우 #000099 색깔로 표시
            # # data 없는 경우 disabled 색깔로 표시
            # STYLE_BUTTON = '''
            #     QPushButton {
            #         background: #000099;
            #         color: white;
            #     }
            #     QPushButton::hover
            #     {
            #         background-color : #6666FF;
            #     }
            #     QPushButton:disabled {
            #         background-color : #999999;
            #     }'''
            
            # # main window 최대화
            # self.setWindowState(QtCore.Qt.WindowMaximized)

            # self.result_layout.count() 가 1이여야 그래프가 tab 의 전체 영역에 출력된다.
            # 이를 위한 예외처리 코드
            # setlayout 후 clear 하고나서 그 후는 addWidget 여러번해도 self.result_layout.count() 는 1
            self.result_layout[TAB_DEFAULT_GRAPH].addWidget(QLabel())
            self.clear_layout(self.result_layout[TAB_DEFAULT_GRAPH])

            # text browser pop up menu
            self.output.setContextMenuPolicy(3)  # Enable custom context menu
            self.output.customContextMenuRequested.connect(self.showContextMenu)

            self.show()

            # # result window 최대화
            # self.win_result.setWindowState(self.win_result.windowState() | QtCore.Qt.WindowMaximized)  # 최대화 설정
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)

    ##########################################################################################
    #   Text Browser Pop up menu
    ##########################################################################################
    def showContextMenu(self, pos):
        context_menu = QMenu(self)
        clear_action = QAction('Clear', self)
        clear_action.triggered.connect(self.clearTextBrowser)
        context_menu.addAction(clear_action)
        # 마우스 우클릭 이벤트가 발생한 위치에 컨텍스트 메뉴를 표시합니다.
        context_menu.exec_(self.output.mapToGlobal(pos))

    ##########################################################################################
    #   Clear contents of the Text Browser
    ##########################################################################################
    def clearTextBrowser(self):
        self.output.clear()

    ##########################################################################################
    #   Menu/Toolbar action
    ##########################################################################################
    def menu_load_strobe_on_off_time(self):
        self.strobe_on_off_time_data_h.load()
    
    def menu_load_mcs_cycle_time(self):
        CycleTimeParserFactory.load_cycle_time(self.mcs_cycle_time)
    
    def menu_load_mcs_pcb_status(self):
        PCBStatusParserFactory.load_pcb_status(self.mcs_pcb_status)

    ##########################################################################################
    # 그래프를 window 에 꽉차게/안차게 표현 
    # param :
    #   checked      icon clicked 여부
    ##########################################################################################
    def resize_full(self, checked):
        # over size 상태에서 resize full 해제안되게, 해제하면 에러 발생
        if self.fig_over_size == True:
            self.actionResizeFull.setChecked(True)
            return
        self.show_result(self.default_graph, self.result_layout[TAB_DEFAULT_GRAPH], checked)
        self.show_result(self.square_wave, self.result_layout[TAB_SQUARE_WAVE], checked)

    ##########################################################################################
    # real time view
    #   주기적으로 호출되어 실시간 그래프 그린다
    ##########################################################################################
    def show_real_time_view(self):
        if self.playing:
            self.click_btn_show()
            # drawing 완료 후에만 thread 돌려서 draw 할 수 있게
            self.worker_thread.run_work()
            
    ##########################################################################################
    # Play real time view for square wave chart
    ##########################################################################################
    def play(self):
        self.playing = True
        self.worker_thread.run_work()   # set event

    ##########################################################################################
    # Pause real time view for square wave chart
    ##########################################################################################
    def pause(self):
        result = True
        msg = ""
        try:        
            self.playing = False
            self.worker_thread.stop_work()      # clear event
            self.actionPlay.setChecked(False)
            # 실시간 그래프 보다가 멈춘 후 그래프에 대한 event 처리
            if self.fig is not None:
                self.set_fig_event(self.fig.axes[0], self.canvas)
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)

    ##########################################################################################
    # Show info
    #   square wave 에서 annote 보여줄지 여부
    ##########################################################################################
    def show_info(self):
        self.showInfo = self.actionInfo.isChecked()

    ##########################################################################################
    # tree widget 의 모든 data 선택
    # param :
    #   tree      tree widet
    ##########################################################################################
    def select_all_data(self, tree:QTreeWidget):
        def select_recursive(item:QTreeWidgetItem):
            item.setSelected(True)
            for i in range(item.childCount()):
                select_recursive(item.child(i))

        for i in range(tree.topLevelItemCount()):
            top_item = tree.topLevelItem(i)
            select_recursive(top_item)

    ##########################################################################################

    ##########################################################################################
    # 초기화 작업
    ##########################################################################################   
    def init(self):
        result = True
        msg = ""
        try:
            self.check_thread.start()
            self.init_strobe_on_off_time()
            self.init_mcs()
            self.init_kyi()
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)
            

    ##########################################################################################
    # module 의 packet buf 내용을 widget 에 move
    # return : packet buf 에 data 있는지 여부
    ##########################################################################################
    def move_packet_buf_to_widget(self, module, packet_type, target, widget):
        result = True
        msg = ""
        try:
            exist_packet_buf_data = False
            buf = module.get_buffer(packet_type)
            if buf:
                exist_packet_buf_data = True
                widget.add_tree_items(buf, target)
                module.clear_packet_buf(packet_type)
            return exist_packet_buf_data
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)

    ##########################################################################################
    # 각 모듈에 data 있는지 판단하여 사용자에게 데이터를 볼 수 있도록 한다
    #   thread 에서 실행된다
    ##########################################################################################       
    def check_data_recv(self):
        result = True
        msg = ""
        try:
            exist_packet_buf_data = False
            while(self.exit is False):
                # context switching 을 하게해서 window msg 전달 빠르게
                QtCore.QCoreApplication.processEvents()
                if self.playing == True:
                    # real time view 경우 tree widget 에 추가하지 않는다
                    time.sleep(1)
                    continue

                # recv_packet_buf -> tree widget 에 move
                self.move_packet_buf_to_widget(self.strobe_on_off_time, PACKET_RECV, TARGET_STROBE_ON_OFF_TIME, self.cmd_tree_widget)
                self.move_packet_buf_to_widget(self.mcs_pcb_status, PACKET_RECV, TARGET_MCS_PCB_STATUS, self.cmd_tree_widget)
                self.move_packet_buf_to_widget(self.mcs_cycle_time, PACKET_RECV, TARGET_MCS_CYCLE_TIME, self.cmd_tree_widget)
                self.move_packet_buf_to_widget(self.kyi, PACKET_RECV, TARGET_KYI, self.cmd_tree_widget)
                
                # 수신된 data 가 있으면 tree 를 expand 하여 scroll bar 나올 수 있게한다.
                if exist_packet_buf_data == True:
                    exist_packet_buf_data = False
                    self.cmd_tree_widget.expandAll()
                    if self.cmd_tree_widget.columnWidth(COLUMN_TIME) > 300 : self.cmd_tree_widget.setColumnWidth(COLUMN_TIME, 300)
                    if self.cmd_tree_widget.columnWidth(COLUMN_NAME) > 100 : self.cmd_tree_widget.setColumnWidth(COLUMN_NAME, 100)
                    if self.cmd_tree_widget.columnWidth(COLUMN_DATA) > 10 : self.cmd_tree_widget.setColumnWidth(COLUMN_DATA, 10)
                    self.cmd_tree_widget.resizeColumnToContents(COLUMN_TIME)
                    self.cmd_tree_widget.resizeColumnToContents(COLUMN_NAME)
                    self.cmd_tree_widget.resizeColumnToContents(COLUMN_DATA)
                
                time.sleep(1)
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)
            
    ##########################################################################################
    # strobe on off time 처리를 위한 초기화 작업 진행
    # return : None
    ##########################################################################################
    def init_strobe_on_off_time(self):
        result = True
        msg = ""
        try:
            self.strobe_on_off_time_data_h.initDdsHandler()
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)
        
    ##########################################################################################
    # MCS PCB Status, cycle time 처리를 위한 초기화 작업 진행
    # return : None
    ##########################################################################################
    def init_mcs(self):
        result = True
        msg = ""
        try:
            for parser in self.pcb_status_parsers:
                parser.initDdsHandler()

            for parser in self.cycle_time_parsers:
                parser.initDdsHandler()

        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)
                
    ##########################################################################################
    # KYI data 처리를 위한 초기화 작업 진행
    # return : None
    ##########################################################################################
    def init_kyi(self):
        result = True
        msg = ""
        try:
            for parser in self.kyi_parsers:
                parser.initDdsHandler()
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)

##########################################################################################

def main():
    try:
        app = QApplication([])
        va = CVisualAnalyzer()

        sys.exit(app.exec_())
    except Exception as ex:
        PRINT_ERR("Exception {}".format(ex))

if __name__ == '__main__':
    # if not pyuac.isUserAdmin():
    #     print("Re-launching as admin!")
    #     pyuac.runAsAdmin()
    # else:        
    #     main()  # Already an admin here.
        
        
    main()