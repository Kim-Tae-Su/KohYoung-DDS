#!/usr/local/bin/python3
# -*- coding: UTF-8 -*-

# DB 제어 관련 Interface

from abc import ABC, abstractmethod


class IDBHandler(ABC):
    @abstractmethod
    def set_data(self, data):
        pass
    
    @abstractmethod
    def clear_buffer(self, type):
        pass

    @abstractmethod
    def get_buffer(self, type):
        pass

    @abstractmethod
    def is_buffer_empty(self, type):
        pass

    # @abstractmethod
    # def get_data(self):
    #     pass