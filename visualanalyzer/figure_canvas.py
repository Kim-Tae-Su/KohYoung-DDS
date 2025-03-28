
#!/usr/local/bin/python3
# -*- coding: UTF-8 -*-

from libs.debug import *
from define import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import traceback


# Figure Canvas 의 event handling
class CFigureCanvasHandler(): 
    def __init__(self):
        self.panning = False
        self.start_x = None
        self.rate = 0.05     # 5%
        self.diff = None  # To track the distance text
        # Lists to store the lines drawn
        self.red_vlines = []
        self.yellow_rectangles = []
        self.drag_rect = []        
    
    ##########################################################################################
    # Ctrl + 마우스 휠 시 axes 확대/축소
    # param :
    #   event       키보드, 마우스 event
    ##########################################################################################    
    def on_scroll(self, event):
        result = True
        msg = ""
        try:
            ax = event.inaxes
            # axes 가 아닌 영역에서는 동작하지 않는다
            if ax is None:
                return

            if event.key == 'control':
                # 전체 구간의 X% 정도씩 확대/축소
                zoom_value = (ax.get_xlim()[1] - ax.get_xlim()[0]) * self.rate
                # PRINT_INFO(f'zoom_value:{zoom_value}, ax.get_xlim()[0]:{ax.get_xlim()[0]}, ax.get_xlim()[1]:{ax.get_xlim()[1]}')
                if event.step > 0:
                    # 마우스 휠 위로하면 확대
                    ax.set_xlim(ax.get_xlim()[0] + zoom_value, ax.get_xlim()[1] - zoom_value)
                elif event.step < 0:
                    # 마우스 휠 아래로하면 축소
                    ax.set_xlim(ax.get_xlim()[0] - zoom_value, ax.get_xlim()[1] + zoom_value)
                plt.draw()
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)

    ##########################################################################################
    # Left mouse button 눌렸을 때 처리
    # param :
    #   event       키보드, 마우스 event
    #   ax_list     axes list
    #   line        line data
    ##########################################################################################  
    def on_button_press(self, event, ax_list = None, lines = None):
        # multi axes 에서 느린 이유
        # axes 개수만큼 func call 된다
        result = True
        msg = ""
        try:
            ax = event.inaxes   # 현재 선택한(마우스 포인터 위치) axes
            if ax is None:
                return
            
            if event.button == 1:  # Left mouse button
                self.panning = True
                self.start_x = event.xdata
                # PRINT_INFO(f'self.start_x:{self.start_x}')
            elif event.button == 3 and ax is not None and lines is not None:  # Right mouse button click
                # event.inaxes
                # Clear previously drawn red lines and yellow rectangles
                for vline in self.red_vlines:
                    vline.remove()
                for rect in self.yellow_rectangles:
                    rect.remove()
                self.red_vlines = []
                self.yellow_rectangles = []

                x_position = self.find_closest_x(event.xdata, ax, lines, event.name)
                # 수직선은 모든 axes 에 다 표시
                for i in range(len(ax_list)):
                  self.red_vlines.append(ax_list[i].axvline(x=x_position, color='r', linestyle='--'))  
                # self.red_vlines.append(ax.axvline(x=x_position, color='r', linestyle='--'))


                self.start_x = x_position
                # PRINT_INFO(f'event.xdata:{event.xdata}, self.start_x:{self.start_x}')
                y_position = max(list(lines.values())[0].get_ydata())

                # 기존 drag_rect 삭제
                self.drag_rect.clear()

                # 노란박스는 모든 axes 에 다 표시
                for i in range(len(ax_list)):
                    self.drag_rect.append(Rectangle((x_position, 0), 0, y_position, alpha=0.5, color='yellow'))
                    self.yellow_rectangles.append(ax_list[i].add_patch(self.drag_rect[i]))
                plt.draw()
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)

    ##########################################################################################
    # Left mouse button 눌렀다가 뗐을 때 처리
    # param :
    #   event       키보드, 마우스 event
    #   ax_list     axes list
    #   line        line data
    ##########################################################################################  
    def on_button_release(self, event, ax_list = None, lines = None):
        result = True
        msg = ""
        try:
            ax = event.inaxes
            if ax is None:
                return

            # PRINT_INFO(f'event.xdata:{event.xdata}')
            if event.button == 1:  # Left mouse button
                self.panning = False
            elif event.button == 3 and lines is not None and self.drag_rect is not None and self.start_x is not None: # right mouse button
                x_position = self.find_closest_x(event.xdata, ax, lines, event.name)
                width = x_position - self.start_x
                
                for i in range(len(self.drag_rect)):
                    self.drag_rect[i].set_width(width)

                # 수직선은 모든 axes 에 다 표시
                for i in range(len(ax_list)):
                    self.red_vlines.append(ax_list[i].axvline(x=x_position, color='r', linestyle='--'))
                # self.red_vlines.append(ax.axvline(x=x_position, color='r', linestyle='--'))
    
                # 숫자를 datetime.datetime 객체로 변환
                diff = abs(mdates.num2date(x_position) - mdates.num2date(self.start_x))

                # Delete the previous diff text, if it exists
                if self.diff:
                    self.diff.remove()
                # Calculate the y position based on the maximum value of the square wave
                max_amplitude = np.max(list(lines.values())[0].get_ydata())
                y_position = max_amplitude / 2
                # Display the diff as a popup text with a white background
                diff_ms = diff.total_seconds() * 1000
                self.diff = ax.text(x_position, y_position, f'{diff_ms} ms', fontsize=10, color='r', backgroundcolor='white', bbox=dict(facecolor='white', edgecolor='none', boxstyle='round'))
                plt.draw()
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)

    ##########################################################################################
    # 마우스 좌우 drag 시 그래프 좌우 이동
    # param :
    #   event       키보드, 마우스 event
    #   line        line data
    ##########################################################################################
    def on_mouse_motion(self, event, line = None):
        result = True
        msg = ""
        try:
            ax = event.inaxes
            if ax is None:
                return
            
            if self.panning:
                current_x = event.xdata
                if current_x is not None and self.start_x is not None:
                    delta_x = current_x - self.start_x
                    # PRINT_INFO(f'delta_x:{delta_x} = current_x:{current_x} - self.start_x:{self.start_x}')
                    ax.set_xlim(ax.get_xlim()[0] - delta_x, ax.get_xlim()[1] - delta_x)
                    # PRINT_INFO(f'ax.get_xlim()[0]:{ax.get_xlim()[0]}, ax.get_xlim()[1]:{ax.get_xlim()[1]}, delta_x:{delta_x}')
                    # PRINT_INFO(f'set_xlim({ax.get_xlim()[0] - delta_x}, {ax.get_xlim()[1] - delta_x})')
                    plt.draw()

            # 마우스 우클릭 드래그 시 노란색 박스
            if event.button == 3 and line is not None and self.drag_rect is not None and self.start_x is not None:
                x_position = self.find_closest_x(event.xdata, ax, line)
                width = x_position - self.start_x
                # PRINT_INFO(f'width:{width} = x_position:{x_position} - event.xdata:{event.xdata}') 
                for i in range(len(self.drag_rect)):
                    self.drag_rect[i].set_width(width)                
                plt.draw()
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)                    

    ##########################################################################################
    # Find the closest x-coordinate in the square wave chart
    #   시작 수직선은 현재 마우스 포인터가 위치한 axes 에서 가장 가까운 그래프에 그린다
    #   종료 수직선은 모든 axes 중에서 마우스 포인터의 x좌표에서 가장 가까운 그래프에 그린다
    # param :
    #   x           현재 마우스 포인터 x 위치
    #   ax          현재 선택된 axes
    #   lines       line data
    #   event_name  event name
    ##########################################################################################    
    def find_closest_x(self, x, ax, lines, event_name = "button_press_event"):
        result = True
        msg = ""
        try:
            closest_x = None
            min_diff = None
            transitions = []

            for ylabel in lines.keys():
                if event_name == 'button_press_event' and ax is not None and ylabel == ax.get_ylabel() or event_name == 'button_release_event':
                    x_data = np.array(lines[ylabel].get_xdata())
                    y_data = lines[ylabel].get_ydata()

                    # Find where y changes
                    # LOW -> HIGH, HIGH -> LOW 변하는 변곡점 위치 찾기
                    for i in range(1, len(y_data)):
                        if y_data[i - 1] != y_data[i]:
                            transitions.append(i)

                    # Convert x_data[transitions] to a NumPy array
                    transition_x_values = x_data[transitions]

                    # Find the closest transition point to the current mouse position
                    diff = min(abs(mdates.date2num(transition_x_values) - x))
                    if min_diff is None or diff < min_diff:
                        min_diff = diff
                        closest_x = transition_x_values[np.argmin(np.abs(mdates.date2num(transition_x_values) - x))]

            # datetime.datetime 객체를 숫자로 변환
            return mdates.date2num(closest_x)
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)          