
#!/usr/local/bin/python3
# -*- coding: UTF-8 -*-

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QTextEdit, QTreeWidget, QTreeWidgetItem, QAction, QMenu
from define import *
from libs.debug import *
import traceback

# 사용자 자료형

# dds data 에 공통으로 있는 data
class CDdsDataHeader:
    def __init__(self, domain = 0, topic = "", cmd = "", time: datetime = 0):
        self.domain = domain
        self.topic = topic
        self.cmd = cmd        
        self.datetime = time        # datetime, ex) 2023/06/16_14:58:53:589
        return None

class COnOffTime:
    def __init__(self, on_time = 0, off_time = 0):
        self.on_time = on_time        # unit : us
        self.off_time = off_time      # unit : us
        return None

# system exception 과 구분하여 exception 처리
class MyException(Exception):
    def __init__(self, message):
        self.message = message

# tree widget
class MyTreeWidget(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabels(["Items"])
        self.setSelectionMode(QTreeWidget.MultiSelection)
        self.setContextMenuPolicy(3)  # Qt.CustomContextMenu
        self.customContextMenuRequested.connect(self.showContextMenu)
        self.initContextMenu()

    # item 에 마우스 우클릭시 팝업 메뉴
    def initContextMenu(self):
        self.removeAction = QAction('Remove', self)
        self.removeAction.triggered.connect(self.removeSelectedItem)
        self.contextMenu = QMenu(self)
        self.contextMenu.addAction(self.removeAction)

    def showContextMenu(self, position):
        self.contextMenu.exec_(self.viewport().mapToGlobal(position))

    # remove seletected item
    def removeSelectedItem(self):
        selected_items = self.selectedItems()
        for item in selected_items:
            parent = item.parent()
            if parent is not None:
                parent.removeChild(item)
            else:
                # 최상위 항목 삭제
                index = self.indexOfTopLevelItem(item)
                self.takeTopLevelItem(index)

    ##########################################################################################
    # 현재 item 의 하위 item 중에 특정 값을 갖는 item 찾기
    # param :
    #   parent_item     이 item 아래에 추가한다
    #   value           찾는 값
    # return :  찾으면 item, 못 찾으면 None
    #   column              column as 0 base
    ########################################################################################## 
    def find_item(self, parent_item: QTreeWidgetItem, value, column = COLUMN_TIME):
        result = True
        msg = ""
        try:         
            for index in range(parent_item.childCount()):
                child_item = parent_item.child(index)
                if child_item.text(column) == str(value):
                    return child_item
            return None
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)

    ##########################################################################################
    # receive packet을 tree widget 에 추가
    # param :
    #   packets     tree widget 에 추가할 packet data 들
    #   target      어떤 module data 인지 구분
    ########################################################################################## 
    def add_tree_items(self, packets, target):
        result = True
        msg = ""
        try:
            if target == TARGET_STROBE_ON_OFF_TIME:
                for packet in packets:
                    item = QTreeWidgetItem(self)
                    item.setText(COLUMN_TIME, str(packet.datetime))
                    item.setText(COLUMN_NAME, str(packet.topic))
                    item.setText(COLUMN_DATA, str(packet.device))                    
            elif target == TARGET_MCS_CYCLE_TIME:
                for packet in packets:
                    item = QTreeWidgetItem(self)
                    item.setText(COLUMN_TIME, str(packet.datetime))
                    item.setText(COLUMN_NAME, str(packet.seq))
                    item.setText(COLUMN_DATA, str(packet.state))                    
            elif target == TARGET_MCS_PCB_STATUS:
                for topic in packets.keys():
                    for packet in packets[topic]:
                        item = QTreeWidgetItem(self)
                        item.setText(COLUMN_TIME, str(packet.datetime))
                        item.setText(COLUMN_NAME, str(packet.status))
                        item.setText(COLUMN_DATA, str(packet.state))
            elif target == TARGET_KYI:
                for packet in packets:
                    item = QTreeWidgetItem(self)
                    item.setText(COLUMN_TIME, str(packet.datetime))
                    item.setText(COLUMN_NAME, str(packet.topic))
                    item.setText(COLUMN_DATA, str(packet.seqId))
            else:
                PRINT_ERR(f'wrong target {target}')
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)
    
    ##########################################################################################
    # Return root item
    ##########################################################################################     
    def get_root_item(self):
        return self.topLevelItem(0)

    ##########################################################################################
    # item 의 column 을 return
    # param :
    #   item        tree item
    ##########################################################################################    
    def get_item_column(self, item : QTreeWidgetItem):
        result = True
        msg = ""
        try:         
            col_count = item.columnCount()
            item_column = 0
            for i in range(col_count):
                if len(item.text(i)) > 0:
                    item_column = i
            return item_column
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)        

# square wave data
class CSquareWaveData:
    def __init__(self, name = "", time: datetime = 0, level = 0):
        self.name = name           # annotate 에 표시할 square wave name
        self.datetime = time
        self.level = level         # voltage High, Low
        return None