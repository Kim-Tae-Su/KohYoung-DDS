#!/usr/local/bin/python3
# -*- coding: UTF-8 -*-
# 그래프 그리는 module

from libs.debug import *
from define import *
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MultipleLocator
from data_type import *
from multipledispatch import dispatch
import copy
import traceback

DUMMY_TIME_MS = 50

class CDraw:
    def __init__(self):
        # {'NOT_EXIST' : [CSquareWaveData, CSquareWaveData, ...],
        #   'PCB_IN_STATUS' : [CSquareWaveData, CSquareWaveData, ...],}        
        self.square_wave_data = dict()      # {str:list[CSquareWaveData]}
        self.square_wave_lines = dict()     # {str:square_wave_data}
        self.VOL_MIN = 0
        self.VOL_MAX = 3
        self.legend_created = False         # 범례 한번만 표시 위함
        self.old_square_wave_count = 0          # topic 이 변경되면 범례 업데이트 위함
        return None

    ##########################################################################################
    # square_wave_data 에 data 추가
    # key:value type으로 value 는 list 로 추가
    # param : 
    #   name        square wave name
    #   time        datetime
    #   level       voltage level, ex) High, Low
    #   data_type   data 종류 구분, 추후 그래프 그릴 때 ylabel 로 사용 됨
    # return :  None
    ########################################################################################## 
    def add_square_wave_data(self, name, time:datetime, level = 0, data_type = ""):
        result = True
        msg = ""
        try:
            if data_type not in self.square_wave_data:
                self.square_wave_data[data_type] = []

            value = CSquareWaveData(name, time, level)
            self.square_wave_data[data_type].append(value)
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)

    ##########################################################################################
    # datetime 순으로 square_wave_data 정렬
    # param : None
    # return :  None
    ########################################################################################## 
    def order_square_wave_data(self):
        result = True
        msg = ""
        try:
            for key in self.square_wave_data.keys():
                # datetime 기준으로 정렬
                self.square_wave_data[key] = sorted(self.square_wave_data[key], key=lambda x: x.datetime)
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)


    ##########################################################################################
    # clear data
    # return :  None
    ########################################################################################## 
    def clear(self):
        self.square_wave_data.clear()
              
    ##########################################################################################
    # Draw square wave chart
    # datetime data로부터 사각 파형 그린다
    # param : 
    #   ax                  그래프 그릴 axes
    #   title               그래프 title
    #   show_annotate       annotate 보여줄지 여부
    #   ylabel              Y축 label
    #   xlabel              X축 label
    #   vol_min             파형의 Low Vol
    #   vol_max             파형의 High Vol
    # return :  None
    ########################################################################################## 
    def draw_square_wave(self, ax, title="", show_annotate = False, ylabel="", xlabel="", vol_min=None, vol_max=None):
        result = True
        msg = ""
        try:
            # if len(self.square_wave_data[ylabel]) == 0:
            #     PRINT_ERR(f'data is empty')
            #     return None
            
            if len(self.square_wave_data) == 0:
                PRINT_ERR(f'data is empty')
                return None
                        
            if vol_min == None:
                vol_min = self.VOL_MIN
            if vol_max == None:
                vol_max = self.VOL_MAX
    
            color_list = ['white', 'green', 'yellow', 'cyan', 'red', 'magenta', 'orange', 'lime', 'purple', 'blue']
            color_list_len = len(color_list)
            square_wave_data_datetime_list = []
            square_wave_list = []       # 범례 출력 순서 바꾸기 위함
            square_wave_name_list = []
            for i, key in enumerate(self.square_wave_data.keys()):
                # Get the square wave data
                if self.get_datetime_list(self.square_wave_data[key], square_wave_data_datetime_list) is not True:
                    raise MyException(f'get_datetime_list failed')

                y_offset = i * 10
                color_ = color_list[i % color_list_len]

                # square wave 생성
                y = []
                # start(state 0) : HIGH
                # end(state 1) : LOW
                for data in self.square_wave_data[key]:
                    data:CSquareWaveData
                    y.append(data.level + y_offset)

                # TODO 화면에 보이는 시간 범위의 데이터만 그린다
                # x축에는 datetime 객체가, y축에는 square wave 값이 오도록 그래프를 그린다
                square_wave, = ax.step(square_wave_data_datetime_list, y, where='post', color=color_, label=key) # memory leak
                # 범례 출력 순서 바꾸기 위함
                square_wave_list.insert(0, square_wave)      
                square_wave_name_list.insert(0, key)

                # ex) find_closest_x 등에서 사용
                # ex) 두 line 간 시간 차 구할 때 사용
                square_wave_line, = ax.plot([], [])
                square_wave_line.set_data(square_wave_data_datetime_list, y)
                square_wave_line.set_visible(False)
                self.square_wave_lines[key] = square_wave_line
                square_wave_data_datetime_list.clear()

            
            # 범례 업데이트는
            # 최초 그릴 때 or topic 개수가 변경 될 때
            if self.legend_created == False or (self.old_square_wave_count != self.square_wave_data.keys()):
                ax.legend(handles=square_wave_list, labels=square_wave_name_list, loc='upper left')
                self.legend_created = True
        
            self.old_square_wave_count = len(self.square_wave_data.keys())

            # x축의 레이블을 날짜와 시간 형식으로 설정
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S.%f'))
            # x축 레이블을 1초 단위로 표시
            ax.xaxis.set_major_locator(mdates.SecondLocator(interval=1))
            ax.xaxis.set_minor_locator(mdates.SecondLocator())

            if title:
                ax.set_title(title, color='white')

            if xlabel:
                ax.set_xlabel(xlabel, color='white')
            if ylabel:
                # y축에 가로로 레이블을 추가
                ax.set_ylabel(ylabel, rotation='horizontal', labelpad=20, color='yellow')

            # Y축 눈금 비우기
            ax.set_yticks([])
            ax.set_facecolor('black')       # grid 배경색
            ax.grid(True, color='black')    # grid 색깔
            ax.tick_params(axis='x', colors='white')    # axis x축 텍스트 색깔

            # annotate  # TODO 여러 topic annote 표시
            # 파형의 start(Low -> High) 신호 위치에 정보 표시
            if show_annotate:
                pre_square_wave_data = None
                for i, square_wave_data in enumerate(self.square_wave_data[ylabel]):
                    square_wave_data:CSquareWaveData
                    if i == 0:
                        if square_wave_data.level == self.VOL_MAX:
                            ax.annotate(f"{square_wave_data.name}", xy=(square_wave_data.datetime, vol_max), xytext=(square_wave_data.datetime, vol_max + 1),
                                        arrowprops=dict(arrowstyle='simple'), fontsize=6, horizontalalignment='left', rotation=45, color='white')
                    else:
                        if pre_square_wave_data.level == self.VOL_MIN and square_wave_data.level == self.VOL_MAX:
                            ax.annotate(f"{square_wave_data.name}", xy=(square_wave_data.datetime, vol_max), xytext=(square_wave_data.datetime, vol_max + 1),
                                        arrowprops=dict(arrowstyle='simple'), fontsize=6, horizontalalignment='left', rotation=45, color='white')
                    pre_square_wave_data = square_wave_data

            # x축 레이블이 겹치지 않도록 회전
            plt.gcf().autofmt_xdate()
        except MyException as ex:
            result = False
            msg = ex            
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result is False:
                PRINT_ERR(msg)


    ##########################################################################################
    # dummy min, max 추가
    # 시작과 끝이 High 상태다 -> 보기 불편 -> 
    # 시작과 끝을 Low 상태로 만들기위해 실제 min 보다 작은(-timedelta_ms) dummy min 추가,
    # 실제 max 보다 큰(+timedelta_ms) dummy max 추가 후 그린다
    # param : 
    #   timedelta_ms        time delta ms
    # return :
    #   dummy min, dummy max
    ########################################################################################## 
    def add_dummy_min_max(self, timedelta_ms = DUMMY_TIME_MS):
        result = True
        msg = ""
        min_datetime = None
        max_datetime = None
        try:
            if len(self.square_wave_data.keys()) == 0:
                PRINT_INFO(f'data is empty')
                return None, None
            
            key_list = list(self.square_wave_data.keys())
            for key in key_list:
                if min_datetime:
                    min_datetime = min(self.get_min_datetime(self.square_wave_data[key]), min_datetime)
                else:
                    min_datetime = self.get_min_datetime(self.square_wave_data[key])
                    
                if max_datetime:
                    max_datetime = max(self.get_max_datetime(self.square_wave_data[key]), max_datetime)
                else:
                    max_datetime = self.get_max_datetime(self.square_wave_data[key])

            dummy_min_datetime = min_datetime - timedelta(milliseconds=timedelta_ms)
            dummy_max_datetime = max_datetime + timedelta(milliseconds=timedelta_ms)
            dummy_min = CSquareWaveData("", dummy_min_datetime)
            dummy_max = CSquareWaveData("", dummy_max_datetime)
            
            for key in key_list:
                self.square_wave_data[key].insert(0, dummy_min)
                self.square_wave_data[key].append(dummy_max)
            
            return dummy_min, dummy_max
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)

    ##########################################################################################
    # real time view 에서 update 시 현재 파형을 보여주기위해 최신 data 와 같은 data 를 dummy 로 추가
    ########################################################################################## 
    def add_dummy(self):
        result = True
        msg = ""
        try:
            if len(self.square_wave_data.keys()) == 0:
                PRINT_DEBUG(f'data is empty')
                return None
            
            key_list = list(self.square_wave_data.keys())
            for key in key_list:
                dummy = copy.deepcopy(self.square_wave_data[key][-1])
                dummy.datetime = datetime.now()
                self.square_wave_data[key].append(dummy)
            
            return None
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)

    ##########################################################################################
    # 모든 그래프 동시에 업데이트하기 위해
    # sqaure wave data 에 있는 최신 시간을 모든 square data 에 추가한다
    ########################################################################################## 
    def align_square_wave_data(self):
        result = True
        msg = ""
        try:
            if len(self.square_wave_data.keys()) == 0:
                PRINT_DEBUG(f'data is empty')
                return None
            
            # sqaure wave data 에 있는 최신 시간 구하기
            max_datetime = None
            max_datetime_key = None     # max datetime 의 key 값
            key_list = list(self.square_wave_data.keys())
            for key in key_list:
                if max_datetime:
                    curr_max_datetime = self.get_max_datetime(self.square_wave_data[key])
                    if curr_max_datetime > max_datetime:
                        max_datetime = curr_max_datetime
                        max_datetime_key = key
                else:
                    max_datetime = self.get_max_datetime(self.square_wave_data[key])
                    max_datetime_key = key

            # 모든 square data 에 최신 시간 추가
            for key in key_list:
                # max datetime 을 가진 square wave 에는 추가로 max datetime 넣지 않는다
                if key is not max_datetime_key:
                    dummy = copy.deepcopy(self.square_wave_data[key][-1])
                    # dummy.datetime = datetime.now()
                    dummy.datetime = max_datetime
                    self.square_wave_data[key].append(dummy)

            return None
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)


    ##########################################################################################
    # square_wave_data[key] 의 datetime 항목 중 최소값 리턴
    # param : 
    #   data        CSquareWaveData type list
    # return : 최소 datetime
    ##########################################################################################
    def get_min_datetime(self, square_wave_data_list:list[CSquareWaveData]):
        result = True
        msg = ""
        try:        
            temp_datetime_list = []
            for square_wave_data in square_wave_data_list:
                temp_datetime_list.append(square_wave_data.datetime)
            return min(temp_datetime_list)
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)


    # 함수 overloading
    @dispatch(dict)
    ##########################################################################################
    # square_wave_data 의 datetime 항목 중 최대값 리턴
    # param : 
    #   data        CSquareWaveData type list
    # return : 최대 datetime
    ##########################################################################################
    def get_max_datetime(self, square_wave_data:dict):
        result = True
        msg = ""
        try:
            # data 없는 경우 현재 시간
            max_datetime = datetime.now()
            key_list = list(square_wave_data.keys())
            for key in key_list:
                if max_datetime:
                    max_datetime = max(self.get_max_datetime(self.square_wave_data[key]), max_datetime)
                else:
                    max_datetime = self.get_max_datetime(self.square_wave_data[key])
            return max_datetime
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)

    @dispatch(list)
    ##########################################################################################
    # square_wave_data[key] 의 datetime 항목 중 최대값 리턴
    # param : 
    #   data        CSquareWaveData type list
    # return : 최대 datetime
    ##########################################################################################
    def get_max_datetime(self, square_wave_data_list:list[CSquareWaveData]):
        result = True
        msg = ""
        try:
            temp_datetime_list = []
            for square_wave_data in square_wave_data_list:
                temp_datetime_list.append(square_wave_data.datetime)
            return max(temp_datetime_list)
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)

    ##########################################################################################
    # square_wave_data[key] 의 datetime 을 list 로 만들어 세팅
    # param : 
    #   square_wave_data_list       CSquareWaveData type list
    #   date_time_list              square_wave_data_list 에서 datetime 만 꺼내서 list 로 세팅
    # return : 
    ##########################################################################################
    def get_datetime_list(self, square_wave_data_list:list[CSquareWaveData], date_time_list:list):
        result = True
        msg = ""
        try:
            for square_wave_data in square_wave_data_list:
                date_time_list.append(square_wave_data.datetime)
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)
            return result
    