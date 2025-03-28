import inspect
from datetime import datetime
import os
from PyQt5 import QtWidgets, QtCore
import logging
import sys
from logging.handlers import RotatingFileHandler
import traceback
from PyQt5.QtCore import Qt
import threading
import time
import queue


PRINT_LEVEL_DEBUG       = 10
PRINT_LEVEL_INFO        = 20
PRINT_LEVEL_WARNING     = 30
PRINT_LEVEL_ERROR       = 40
PRINT_LEVEL_CRITICAL    = 50

# Create logger
logger = logging.getLogger()

# 로그 레벨 설정 (DEBUG, INFO, WARNING, ERROR, CRITICAL), 세팅 LEVEL 이상만 logging
logger.setLevel(logging.INFO)

# output format
formatter = logging.Formatter('%(message)s')

# stream handler
streamHandler = logging.StreamHandler(sys.stdout)
streamHandler.setFormatter(formatter)

LOG_FOLDER = '.\\log'
LOG_FILE = LOG_FOLDER + '\\VA.log'

# log 폴더 없으면 만들기
if not os.path.exists(LOG_FOLDER):
    os.mkdir(LOG_FOLDER)

# RotatingFileHandler 생성
max_bytes = 1048576     # 각 로그 파일의 최대 크기 (바이트 단위)
backup_count = 5        # 유지할 백업 로그 파일의 개수
fileHandler = RotatingFileHandler(LOG_FILE, maxBytes=max_bytes, backupCount=backup_count, mode='a')
fileHandler.setFormatter(formatter)

# add handler
logger.addHandler(streamHandler)
logger.addHandler(fileHandler)

global outputh
outputh: QtWidgets.QListWidget = None    

data_q = queue.Queue()

class CPrintThread():
    def __init__(self):
        try:        
            self.exit_thread = False            # thread loop 종료시키기
            self.print_thread = threading.Thread(target=self.do_work, args=(data_q,))
            self.print_thread.start()
        except Exception as ex:
            err_msg = "{}".format(traceback.format_exc())
            print(err_msg)

    ##########################################################################################
    # print 에 오래 걸리는 작업을 thread 에서 실행
    ##########################################################################################
    def do_work(self, q):
        try:
            while self.exit_thread is False:
                QtCore.QCoreApplication.processEvents()
                while not q.empty():
                    QtCore.QCoreApplication.processEvents()
                    value = q.get()
                    self.print_msg(value[0], value[1])
                    q.task_done()
                time.sleep(1)
        except Exception as ex:
            err_msg = "{}".format(traceback.format_exc())
            print(err_msg)
    
    ##########################################################################################
    # UI(widget) 또는 터미널에 log 출력 및 log file 에 log 출력
    ##########################################################################################    
    def print_msg(self, msg: str, print_level: int):
        try:        
            if print_level >= PRINT_LEVEL_ERROR:
                item_color = Qt.red
            else:
                item_color = Qt.black

            if print_level >= PRINT_LEVEL_INFO:
                # ouput widget 에 msg 출력
                if outputh != None:
                    item = QtWidgets.QListWidgetItem(msg)
                    item.setForeground(item_color)
                    outputh.addItem(item)
                    # 항상 마지막 데이터가 보이도록 스크롤 조정
                    current_row = outputh.count() - 1
                    outputh.setCurrentRow(current_row)

                    # memory leak 방지위해 로그가 5000개 넘으면 제일 오래된 item 삭제
                    if outputh.count() > 5000:
                        # Remove the first item
                        item_to_remove = outputh.takeItem(0)
                        # Make sure to delete the removed item to free up memory
                        del item_to_remove
            else:
                # PRINT_LEVEL_DEBUG 는 터미널에 출력
                print(msg)

            if print_level == PRINT_LEVEL_CRITICAL:
                logger.critical(msg)
            elif print_level == PRINT_LEVEL_ERROR:
                logger.error(msg)
            elif print_level == PRINT_LEVEL_WARNING:
                logger.warning(msg)
            elif print_level == PRINT_LEVEL_INFO:
                logger.info(msg)
            elif print_level == PRINT_LEVEL_DEBUG:
                logger.debug(msg)
        except Exception as ex:
            err_msg = "{}".format(traceback.format_exc())
            print(err_msg)
                        
    # 객체 삭제 전 객체 내 thread 먼저 종료해야한다
    def finalize(self):
        try:            
            # thread loop 종료시키기
            self.exit_thread = True
            # thread 종료 대기
            self.print_thread.join()
        except Exception as ex:
            err_msg = "{}".format(traceback.format_exc())
            print(err_msg)

def PRINT_DEBUG(msg):
    PrintMsg(msg, PRINT_LEVEL_DEBUG)
    
def PRINT_INFO(msg):
    PrintMsg(msg, PRINT_LEVEL_INFO)
    
def PRINT_WARN(msg):
    PrintMsg(msg, PRINT_LEVEL_WARNING)
    
def PRINT_ERR(msg):
    PrintMsg(msg, PRINT_LEVEL_ERROR)

def PRINT_CRITICAL(msg):
    PrintMsg(msg, PRINT_LEVEL_CRITICAL)
    
# main winodw 의 QListWidget 에 msg 출력하기위해 해당 widget 의 handle 을
# 이 module 의 다른 함수에서 사용할 수 있도록 global 로 handle 을 세팅
def SetOutputHandle(handle: QtWidgets.QListWidget):
    global outputh
    outputh = handle

##########################################################################################
# log 에 추가 정보(시간, file name, func name, line num 등) 추가
##########################################################################################    
def PrintMsg(msg: str, print_level: int):
    try:
        msg = str(msg)
        f = inspect.currentframe()
        i = inspect.getframeinfo(f.f_back.f_back)

        # 현재 날짜와 시간(micro sec)을 가져옵니다
        now = datetime.now()
        formatted_datetime_with_millisecond = f"""{now:%Y-%m-%d %H:%M:%S}.{"{:03d}".format(now.microsecond // 1000)}"""

        if print_level >= PRINT_LEVEL_ERROR:
            msg = formatted_datetime_with_millisecond + ' [' + os.path.basename(i.filename) + '] [' + i.function + '] [' + str(i.lineno) + '] [ERR] ' + msg
        elif print_level >= PRINT_LEVEL_INFO:
            msg = formatted_datetime_with_millisecond + ' [' + os.path.basename(i.filename) + '] [' + i.function + '] [' + str(i.lineno) + '] ' + msg
        else:
            # PRINT_LEVEL_INFO 이상만 ouput widget 에 msg 출력
            msg = formatted_datetime_with_millisecond + ' [' + os.path.basename(i.filename) + '] [' + i.function + '] [' + str(i.lineno) + '] ' + msg

        data_q.put((msg, print_level))
    except Exception as ex:
        err_msg = "{}".format(traceback.format_exc())
        print(err_msg)