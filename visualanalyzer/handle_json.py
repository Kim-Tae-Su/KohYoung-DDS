
#!/usr/local/bin/python3
# -*- coding: UTF-8 -*-

from threading import Lock
import json
from libs.debug import *
import traceback
from abc import ABC, abstractmethod
MODE_OVERWRITE = 0      # 기존 file 에 overwrtie
MODE_APPEND = 1         # 기존 file 내용에 append


class CExportFileManager:

    @abstractmethod
    def write_file(self):
        pass


class CJasonManager:
    lock = threading.Lock()

    def __init__(self, name = ''):
        
        # self.lock = threading.Lock()
        self.name = name
        
    @staticmethod
    def read_file(file_path):
        result = True
        msg = ""
        try:
            with open(file_path, 'r', encoding='UTF-8') as file:
                json_data = json.load(file)
                return json_data
        except (FileNotFoundError, json.JSONDecodeError) as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)

    def write_file(self, data, file_path, option = MODE_APPEND):
        result = True
        msg = ""
        try:

            #print('----> WriteFile Start : Name:{}\n'.format(self.name))

            CJasonManager.lock.acquire() #뮤텍스 잠금

            #print('----> WriteFile ... : Name:{}\n'.format(self.name))
            try:
                if option == MODE_OVERWRITE:
                    with open(file_path, 'w', encoding='UTF-8') as file:
                        json.dump(data, file, indent=4, ensure_ascii=False)
                    return None
                else:
                    # Try to read the existing data from the file
                    with open(file_path, 'r', encoding='UTF-8') as file:
                        existing_data = json.load(file)
            except (FileNotFoundError, json.JSONDecodeError):
                # 파일이 있는 디렉토리 경로
                directory_path = os.path.dirname(file_path)

                # 디렉토리 경로가 없으면 생성
                if not os.path.exists(directory_path):
                    os.makedirs(directory_path)
            
                # 파일이 존재하지 않는 경우 빈 리스트로 시작합니다.
                existing_data = []

            # 기존 데이터와 추가 데이터를 합쳐서 새로운 데이터를 만듭니다.
            new_data = existing_data + data

            # 새로운 데이터를 파일에 저장합니다.
            with open(file_path, 'w', encoding='UTF-8') as file:
                json.dump(new_data, file, indent=4, ensure_ascii=False)
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                PRINT_ERR(msg)

        #print('----> unlock : Name:{}\n'.format(self.name))
        CJasonManager.lock.release()
        #print('----> WriteFile End : Name:{}\n'.format(self.name))