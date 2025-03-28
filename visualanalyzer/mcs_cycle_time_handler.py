
#!/usr/local/bin/python3
# -*- coding: UTF-8 -*-


from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from libs.debug import *
import copy
from define import *
from data_type import *
from db_handler import *
# # 마우스 휠로 확대/축소 동작 가능, Agg 는 안됨
import matplotlib
matplotlib.use('QtAgg')
from figure_canvas import *
import traceback

import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import mean_squared_error , r2_score
import joblib

MCS_CYCLE_TIME_START = 0
MCS_CYCLE_TIME_END = 1

LINE_WIDTH = 10


class CCycleTimeData(CDdsDataHeader): 
    def __init__(self, domain = 0, topic = "", cmd = "", time: datetime = 0, seq = "", state = 0):
        super().__init__(domain, topic, cmd, time)
        self.seq = seq
        self.state = state
        return None
    
class CFovMovingTimeData(CDdsDataHeader): 
    def __init__(self, domain = 0, topic = "", cmd = "", time: datetime = 0, seq = "", state = 0, coordinate = ()):
        super().__init__(domain, topic, cmd, time)
        self.seq = seq
        self.state = state
        self.coordinate=coordinate
        return None

class CMcsCycleTime(CDBHandler, CFigureCanvasHandler):
    def __init__(self, data_holder):
        CFigureCanvasHandler.__init__(self)
        # 수신 packet, show list 로 옮겨진다
        self.recv_packet_buf: list[CCycleTimeData] = list()
        # 모든 수신 packet
        self.all_packet_buf: list[CCycleTimeData] = list()
        # 그래프로 출력할 packet
        self.show_packet_buf: list[CCycleTimeData] = list()
        # error seq 구분
        self.error_seq: list[str] = list()
        self.target = TARGET_MCS_CYCLE_TIME
        self.data_file = "./db/mcs_cycle_time.json"
        self.fig_width_size_inch = 14
        self.fig_height_size_inch = 7
        # 데이터 프레임
        self.dataholder=data_holder
        
        return None

    ##########################################################################################
    # Add packet of cycle time
    # param :
    #   packet         packet of cycle time
    #   packet_type    packet type
    # return : None
    ##########################################################################################
    def add_packet(self, packet: CCycleTimeData, packet_type):
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
    # packet list 에서 datetime 이 제일 빠른 것 찾기
    #   data 없으면 return None
    # param : 
    #   pcb_status_list          pcb status data list
    ##########################################################################################
    def get_earliest_time(self, cmd_list: list[CCycleTimeData]):
        time_list = []
        for data in cmd_list:
            time_list.append(data.datetime)
        if len(time_list) > 0:
            return min(time_list)
        return None

    ##########################################################################################
    # Seqeunce 에 따라 color 값 리턴
    # param : 
    #   seq          sequence
    # return : None
    ##########################################################################################
    def get_color(self, seq):
        color = 'green'
        if 'OPRUN' in seq:
            color = 'red'
        elif 'TURNAROUND_TIME' in seq:
            color = 'green'
        elif 'TRANSFER_TIME' in seq:
            color = 'blue'
        elif 'LANE_INSP' in seq:
            color = 'cyan'
        elif 'PCB_INSP' in seq:
            color = 'yellow'
        elif 'FID_MOVE' in seq:
            color = 'black'
        elif 'FID_INSP' in seq:
            color = 'magenta'
        elif 'FOV_MOVE' in seq:
            color = 'orange'
        elif 'FOV_INSP' in seq:
            color = 'purple'
        elif 'SMEMA' in seq:
            color = 'lime'
        return color
    
    ##########################################################################################
    # Sequence 를 start end 쌍을 맞춰서 재정렬함
    #   ex) A0 B0 B1 A1 -> A0 A1 B0 B1 으로 변경하는게 낫다
    # param : 
    #   packet_buf          packet buf
    # return : ordered cycle time data
    ##########################################################################################
    def get_ordered_data(self, packet_buf:list[CCycleTimeData]):
        ordered_data: list[CCycleTimeData] = list()
        temp_cmd_list = copy.deepcopy(packet_buf)
        for i, data in enumerate(temp_cmd_list):
            if data.state == MCS_CYCLE_TIME_START:
                ordered_data.append(data)
                # state 가 end 인 data 찾는다
                found_data = self.get_data_by_seq_state(temp_cmd_list, i, data.seq, MCS_CYCLE_TIME_END)
                if found_data == None:
                    # state 가 start 만 오고 end 는 안온 경우 예외 처리                    
                    PRINT_INFO(f"not found end data for {data.seq}, do exception handle")
                    found_data = copy.deepcopy(data)
                    found_data.state = MCS_CYCLE_TIME_END
                    ordered_data.append(found_data)
                    self.error_seq.append(found_data.seq)
                else:
                    ordered_data.append(found_data)
                    found_index = temp_cmd_list.index(found_data)
                    # 새로 추가된 data 에 대해서는 pair 추가 작업하지 않는다. -> 중복 data 발생 방지
                    del temp_cmd_list[found_index]
            else:
                # state 가 start 인 data 찾는다
                found_data = self.get_data_by_seq_state(temp_cmd_list, i, data.seq, MCS_CYCLE_TIME_START)
                if found_data == None:
                    # state 가 end 만 오고 start 는 안온 경우 예외 처리                    
                    PRINT_INFO(f"not found start data for {data.seq}, do exception handle")
                    found_data = copy.deepcopy(data)
                    found_data.state = MCS_CYCLE_TIME_START
                    ordered_data.append(found_data)
                    self.error_seq.append(found_data.seq)
                else:
                    ordered_data.append(found_data)
                    found_index = temp_cmd_list.index(found_data)
                    # 새로 추가된 data 에 대해서는 pair 추가 작업하지 않는다. -> 중복 data 발생 방지
                    del temp_cmd_list[found_index]
                                        
                ordered_data.append(data)

        return ordered_data

    ##########################################################################################    
    # datetime, name 으로 packet 을 찾는다
    # param :
    #   datetime_obj    datetime
    #   name            찾을 data name
    # return : 찾으면 packet, 못 찾으면 None
    ##########################################################################################    
    def get_packet(self, datetime_obj, name) -> CCycleTimeData:
        result = True
        msg = ""
        try:
            for packet in self.all_packet_buf:
                if packet.datetime == datetime_obj and packet.seq == name:
                    return packet
            raise MyException(f'{datetime_obj} {name} is not exist')
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
    # all_packet_buf list 의 index 번째 packet 제거
    # param :
    #   index    all_packet_buf list 의 index
    ##########################################################################################
    def del_packet(self, index):
        result = True
        msg = ""
        try:
            if index >= len(self.all_packet_buf):
                raise MyException(f'index {index} >= self.all_packet_buf len {len(self.all_packet_buf)}')
            del self.all_packet_buf[index]
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
    # packet buf 에서 seq 이고 state 가 parameter state 인 data 를 return
    #   해당되는 data 가 없으면 return None
    # param : 
    #   packet_buf            packet buf
    #   start_index         list 내의 start index
    #   seq                 sequence
    #   state               찾을 data 의 state
    # return : cycle time data
    ##########################################################################################
    def get_data_by_seq_state(self, packet_buf:list[CCycleTimeData], start_index, seq, state):
        result = True
        msg = ""
        try:
            cmd_len = len(packet_buf)
            for i in range(cmd_len):
                if i + start_index >= cmd_len:
                    break
                else:
                    if packet_buf[i + start_index].seq == seq and packet_buf[i + start_index].state == state:
                        return packet_buf[i + start_index]
            return None
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)
                        
    ##########################################################################################
    # packet 의 state의 start, end 쌍을 맞춘다
    #   start 만 온 경우 end 추가, end 만 온 경우 start 추가
    # ex) data 미수신이던 사용자가 선택을 안했던, show 할 때는 start, end 쌍을 맞춰야
    # 그래프가 표시된다.
    # packet 의 state가 start 만 오고 end 가 없는 경우가 있다.
    # 
    # param :
    #   cmd_list          cycle time list
    ##########################################################################################
    def make_pair_state(self, cmd_list: list[CCycleTimeData]):
        result = True
        msg = ""
        try:
            for data in cmd_list:
                if data.state == MCS_CYCLE_TIME_START:
                    # state 가 end 인 data 찾는다
                    found_data = self.get_data_by_seq_state(cmd_list, 0, data.seq, MCS_CYCLE_TIME_END)
                    if found_data == None:
                        # state 가 start 만 오고 end 는 안온 경우 예외 처리                    
                        PRINT_ERR(f"not found end data for {data.seq}, do exception handle")
                        found_data = copy.deepcopy(data)
                        found_data.state = MCS_CYCLE_TIME_END
                        # 기존 packet list 에 dummy 추가
                        cmd_list.append(found_data)
                        self.error_seq.append(found_data.seq)
                    else:
                        pass
                elif data.state == MCS_CYCLE_TIME_END:
                    # state 가 start 인 data 를 list 처음부터 찾는다
                    found_data = self.get_data_by_seq_state(cmd_list, 0, data.seq, MCS_CYCLE_TIME_START)
                    if found_data == None:
                        # state 가 end 만 오고 start 는 안온 경우 예외 처리                    
                        PRINT_ERR(f"not found start data for {data.seq}, do exception handle")
                        found_data = copy.deepcopy(data)
                        found_data.state = MCS_CYCLE_TIME_START
                        # 기존 packet list 에 dummy 추가
                        cmd_list.append(found_data)
                        self.error_seq.append(found_data.seq)
                    else:
                        pass
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)
                        
    ##########################################################################################
    # Sequence 가 종료되는 datetime 정보 얻기, index i부터 조사
    # param : 
    #   layout              그래프 추가할 layout
    # return : scene 에 다음에 추가할 postion y
    ##########################################################################################
    def show(self, layout):      
        result = True
        msg = ""
        try:
            # 기존 error packet 제거
            self.error_seq.clear()
            
            labels_start = []
            x_values_start = []
            x_values_end = []
            y_values = []
            
            first_time = self.get_earliest_time(self.show_packet_buf)
            
            # packet 의 state의 start, end 쌍을 맞춘다
            self.make_pair_state(self.show_packet_buf)

            # 기존 소스 이용하려면
            # A0 B0 B1 A1 -> A0 A1 B0 B1 으로 변경하는게 낫다
            self.show_packet_buf = self.get_ordered_data(self.show_packet_buf)
            
            # 원본 데이터에서 시작 데이터와 종료 데이터로 구분한다.
            # 수평선 그리기와 수평선 옆에 문구 추가 목적
            for data in self.show_packet_buf:
                time_ms = int((data.datetime - first_time).total_seconds() * 1000)  # ms
                if data.state == MCS_CYCLE_TIME_START:
                    labels_start.append(data.seq)
                    x_values_start.append(time_ms)      # ms
                else:
                    x_values_end.append(time_ms)        # ms
            
            # y축 event
            y_values = range(len(x_values_start))

            # 새로운 fig, ax 에 그래프 그리기
            fig, ax = plt.subplots(1, 1, figsize=(self.fig_width_size_inch, self.fig_height_size_inch))

            # Create a FigureCanvas for the current figure
            canvas = FigureCanvas(fig)

            # event.key 가 none 으로 나오는 문제 수정
            canvas.setFocusPolicy(QtCore.Qt.ClickFocus)
            canvas.setFocus()
            
            ax.set_title('MCS cycle time')
            ax.set_xlabel('time(ms)')
            ax.set_ylabel('')
            
            for i in range(len(x_values_start)):
                ax.hlines(y_values[i], xmin=x_values_start[i] , xmax=x_values_end[i], colors=self.get_color(labels_start[i]), linestyles='solid', linewidth=LINE_WIDTH)

            # 수평선 왼쪽에 시작 문구 추가
            for x, y, label in zip(x_values_start, y_values, labels_start):
                # state 가 start 만 오고 end 가 안 온 경우 text 색깔 다르게
                if label in self.error_seq:
                    ax.text(x, y, label, ha='right', va='center', fontdict=text_font_err)
                else:
                    ax.text(x, y, label, ha='right', va='center', fontdict=text_font)
            
            # 눈금 비우기
            ax.set_yticks([])
            
            # fig.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)

            canvas.mpl_connect('scroll_event', self.on_scroll)
            canvas.mpl_connect('button_press_event', self.on_button_press)
            canvas.mpl_connect('button_release_event', self.on_button_release)
            canvas.mpl_connect('motion_notify_event', self.on_mouse_motion)

            layout.addWidget(canvas)
            return None
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)

                                    
    ##########################################################################################
    # Machine Learning Data Variance Show
    # param : 
    # layout              그래프 추가할 layout
    # return 
    ##########################################################################################
    def show_analysis1(self, layout):      
        result = True
        msg = ""
        try:
            self.error_seq.clear()
            
            df=self.dataholder.df

            # 새로운 fig, ax 에 그래프 그리기
            fig, axs = plt.subplots(nrows=1, ncols=2, figsize=(self.fig_width_size_inch, self.fig_height_size_inch))
            
            lm_features = ['x_coordinate','y_coordinate']
            for i , feature in enumerate(lm_features):
                # 시본의 regplot을 이용해 산점도와 선형 회귀 직선을 함께 표현
                sns.regplot(x=feature , y='time', data=df , ax=axs[i])
           
            # Create a FigureCanvas for the current figure
            canvas = FigureCanvas(fig)
            layout.addWidget(canvas)
            return None
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)
                
    ##########################################################################################
    # Machine Learning Data 기반해서 예측한 데이터와 실제 데이터값 Show
    # param : 
    # layout              그래프 추가할 layout
    # return 
    ##########################################################################################    
    def show_analysis2(self, layout):      
        result = True
        msg = ""
        try:
        # 기존 error packet 제거
            self.error_seq.clear()
            
            x_coordinate = []
            y_coordinate = []
            start_time=[]
            end_time=[]
            
            for data in self.show_packet_buf:
                if(data.seq == 'FOV_MOVE'):
                    if(data.state==0):
                        start_time.append(data.datetime)
                    else:
                        end_time.append(data.datetime)
                        x_coordinate.append(float(data.coordinate[0]))
                        y_coordinate.append(float(data.coordinate[1]))
                    
            x_coordinate=np.array(x_coordinate)
            y_coordinate=np.array(y_coordinate)
            
            coordinate=np.vstack([x_coordinate, y_coordinate]).T
            
            start_time=np.array(start_time)
            end_time=np.array(end_time)
            sorted_start_indices=np.argsort(start_time)
            sorted_start_time = start_time[sorted_start_indices]
            sorted_end_indices=np.argsort(end_time)
            sorted_end_time = end_time[sorted_end_indices]
            
            time_diff=sorted_end_time-sorted_start_time
            
            # Test 데이터 프레임 생성
            df=pd.DataFrame(coordinate, columns=['x_coordinate', 'y_coordinate'])
            df['x_coordinate'] = abs(df['x_coordinate'].diff())
            df['y_coordinate'] = abs(df['y_coordinate'].diff())
            
            df['time']=time_diff
            df['time']=df['time'].dt.total_seconds() * 1000
            
            df['fid_start_diff']=sorted_start_time
            df['fid_start_diff']=df['fid_start_diff'].diff()
            
            # print(df)
            # first index remove
            df.dropna(inplace=True)
            # repeat first index remove
            df = df[df['fid_start_diff'] < pd.Timedelta(seconds=1)]
            # unncesspry data remove
            df.drop(['fid_start_diff'], axis=1, inplace=True)
            # Reset the index and drop the existing index
            df.reset_index(drop=True, inplace=True)
            
            # print(df)
            # 실제 Time 데이터
            X_test = df.drop(['time'], axis=1, inplace=False)
            y_test = df['time']
            
            # Linear Regression 모델 예측 Time 데이터
            linear_moder=self.dataholder.lr_model
            y_preds = linear_moder.predict(X_test)
            mse = mean_squared_error(y_test, y_preds)
            rmse = np.sqrt(mse)
            r2 = r2_score(y_test, y_preds)
            
            # Scaled Polynomial Ridge 모델 예측 Time 데이터
            # x_scaler=self.dataholder.x_scaler
            # y_scaler=self.dataholder.y_scaler
            # Test 값 로그 스케일링
            log_feature=np.log1p(X_test)
            # Test 값 예측 및 원상복구
            poly_model=joblib.load('./db/model.pkl')
            
            
            log_target_preds=poly_model.predict(log_feature)
            y_preds_poly = np.expm1(log_target_preds)
            
            mse_poly=mean_squared_error(y_test, y_preds_poly)
            rmse_poly = np.sqrt(mse_poly)
            r2_poly = r2_score(y_test, y_preds_poly)
            
            # 시각화
            fig, axs = plt.subplots(nrows=1, ncols=2,figsize=(self.fig_width_size_inch, self.fig_height_size_inch), subplot_kw={'projection': '3d'})
            # Linear Regression Model Actual & Predicted
            axs[0].scatter(X_test['x_coordinate'].values, X_test['y_coordinate'].values, y_test.values, c='blue', marker='o', label='Actual')
            axs[0].scatter(X_test['x_coordinate'].values, X_test['y_coordinate'].values, y_preds, c='red', marker='x', label='Predicted')
           
            x_range = np.linspace(0, max(X_test['x_coordinate'].values), 100)
            y_range = np.linspace(0, max(X_test['y_coordinate'].values), 100)
            x1_mesh, x2_mesh = np.meshgrid(x_range, y_range)
            regression_plane = linear_moder.coef_[0] * x1_mesh + linear_moder.coef_[1] * x2_mesh + linear_moder.intercept_
            axs[0].plot_surface(x1_mesh,x2_mesh,regression_plane,color='green',alpha=0.3,rstride=100,cstride=100,label=f"Intercept : {np.round(linear_moder.intercept_,2)},W : {np.round(linear_moder.coef_,2)}")
            
            axs[0].scatter([], [], [], label=f"RMSE : {rmse:.2f}, Variance score : {r2:.2f}")
            
            axs[0].set_xlabel('X (Independent Variable)')
            axs[0].set_ylabel('Y (Independent Variable)')
            axs[0].set_zlabel('Time (Dependent Variable)')
            axs[0].set_xlim(0, max(X_test['x_coordinate'].values))
            axs[0].set_ylim(0, max(X_test['y_coordinate'].values))
            axs[0].set_zlim(100, max(y_test.values))
            axs[0].set_title('Linear Regression Model')
            axs[0].legend()
            
            # TS 요구사항 FOV 무빙 타임 2차원으로 시각화####################################################
            # fig, axs = plt.subplots(nrows=1, ncols=2,figsize=(self.fig_width_size_inch, self.fig_height_size_inch))
            # data = pd.DataFrame({
            #        'Index': np.arange(len(y_test.values)),
            #        'Actual': y_test.values,
            #        'Predicted': y_preds_poly
            #                 })

            # # Seaborn 바플롯 그리기
            # sns.barplot(x='Index', y='value', hue='variable', data=pd.melt(data, id_vars='Index'))
            ###############################################################################################
            
            # Polynomial Ridge Model Actual & Predicted
            axs[1].scatter(X_test['x_coordinate'].values, X_test['y_coordinate'].values, y_test.values, c='blue', marker='o', label='Actual')
            axs[1].scatter(X_test['x_coordinate'].values, X_test['y_coordinate'].values, y_preds_poly, c='red', marker='x', label='Predicted')
           
            # axs[1].scatter([], [], [], label=f"Intercept : {np.round(poly_model.named_steps['Ridge'].intercept_,2)},W : {np.round(poly_model.named_steps['Ridge'].coef_,2)}")
            axs[1].scatter([], [], [], label=f"RMSE : {rmse_poly:.2f}, Variance score : {r2_poly:.2f}")
            
            axs[1].set_xlabel('X (Independent Variable)')
            axs[1].set_ylabel('Y (Independent Variable)')
            axs[1].set_zlabel('Time (Dependent Variable)')
            axs[1].set_xlim(0, max(X_test['x_coordinate'].values))
            axs[1].set_ylim(0, max(X_test['y_coordinate'].values))
            axs[1].set_zlim(100, max(y_preds_poly))
            axs[1].set_title('Scaled Polynomial Ridge Model')
            axs[1].legend()
            
            # Create a FigureCanvas for the current figure
            canvas = FigureCanvas(fig)
            layout.addWidget(canvas)
            return None
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)