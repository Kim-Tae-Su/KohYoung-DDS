

from handle_json import *
from abc import ABC, abstractmethod
import threading
import queue
from PyQt5 import QtCore 
import time
import traceback

DATETIME_FORMAT = "%Y/%m/%d_%H:%M:%S:%f"

class CDataExportThread(ABC):
    def __init__(self):
        self.data_q = queue.Queue() 
        self.exit_thread = False                           # thread loop 종료시키기
        self.shared_export_thread = None
        self.event_topic_receive_wait = threading.Event()
        self.initialize_shared_export_thread()             # Ensure the shared thread is started
        
         
    #Interfaces
    @abstractmethod
    def export_data(self, *args):
        pass

    #Interfaces
    def add_data(self, data):
        result = True
        msg = ""
        try:
            self.data_q.put(data)
            self.event_topic_receive_wait.set()
        except MyException as ex:
            result = False
            msg = ex
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result is False:
                PRINT_ERR(msg)
    
    def finalize(self):
        result = True
        msg = ""
        try:
            self.exit_thread = True
            self.event_topic_receive_wait.set()
            if self.shared_export_thread is not None:
                self.shared_export_thread.join()
                
        except MyException as ex:
            result = False
            msg = ex
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result is False:
                PRINT_ERR(msg)
                

    def initialize_shared_export_thread(self):
        result = True
        msg = ""
        try:
            self.exit_thread = False                           # thread loop 종료시키기
            if self.shared_export_thread is None:
                self.shared_export_thread = threading.Thread(target=self.data_export_thread)
                self.shared_export_thread.start()
                
        except MyException as ex:
            result = False
            msg = ex
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result is False:
                PRINT_ERR(msg)


    def data_export_thread(self):
        result = True
        msg = ""
        try:
            while(self.exit_thread == False):
                result = True
                try:
                    self.event_topic_receive_wait.wait()
                    if self.exit_thread == True:
                        break #종료시 큐에 데이터가 있을때 모두 처리하고 종료할 것인지.. 아니면 바로 종료할 것인지는 정책 필요.

                    while not self.data_q.empty():                        
                        value = self.data_q.get_nowait()
                        self.export_data(value)
                        self.data_q.task_done()
                        QtCore.QCoreApplication.processEvents()
                        
                    self.event_topic_receive_wait.clear()

                except MyException as ex:
                    result = False
                    msg = ex
                except Exception as ex:
                    result = False
                    msg = "{}".format(traceback.format_exc())
                finally:
                    if result is False:
                        PRINT_ERR(msg)
                
        except MyException as ex:
            result = False
            msg = ex
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result is False:
                PRINT_ERR(msg)