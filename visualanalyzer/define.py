#!/usr/local/bin/python3
# -*- coding: UTF-8 -*-

# 소스에서 공통적으로 사용되는 define

text_font = {
    'fontsize': 6,
    'fontweight': 'bold',
    'color' : 'black'
}

text_font_err = {
    'fontsize': 6,
    'fontweight': 'bold',
    'color' : 'red'
}

# DDS 로부터 수신된 packet data 종류 구분
# add packet 함수를 하나로 하기 위함
PACKET_ALL_TYPE = -1    # 모든 packet type, clear 시 모든 type(recv,all,show)를 삭제위해 사용
PACKET_RECV = 0         # DDS 로부터 수신된 packet data, tree 로 보여주고 삭제된다
PACKET_ALL = 1          # DDS 로부터 수신된 packet data, 누적된다, 20231102 현재 삭제 시나리오 없다 TODO 삭제 언제?
PACKET_SHOW = 2         # tree 에서 사용자가 선택한 packet data, 그래프 출력 후 삭제된다

# data 구분
TARGET_STROBE_ON_OFF_TIME   = 0
TARGET_MCS_PCB_STATUS       = 1
TARGET_MCS_CYCLE_TIME       = 2
TARGET_KYI                  = 3

# tree widget column
COLUMN_TIME     = 0
COLUMN_NAME      = 1
COLUMN_DATA        = 2

# inch 당 scene pos y 위치에 다음 item 추가한다
SCENE_POS_Y_PER_INCH = 100

# MSC topic 의 state 가 0 : start, 1 : end
MCS_STATE_START = 0
MCS_STATE_END = 1