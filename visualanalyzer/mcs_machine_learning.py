import pandas as pd
import numpy as np
from datetime import datetime

from sklearn.linear_model import LinearRegression, Ridge
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeRegressor
from xgboost import XGBRegressor

import seaborn as sns
import matplotlib.pyplot as plt

import joblib

import traceback

DATETIME_FORMAT = "%Y/%m/%d_%H:%M:%S:%f"

class CMcsMachineLearning():
    def __init__(self):
        self.raw_df=self.load_data()
        self.df=None
        self.lr_model=None
        self.poly_model=None
        self.x_scaler=None
        self.y_scaler=None
        
    def load_data(self):
        return pd.read_json('./db/fov_machine_learning.json')
        
    def feature_engineer(self):
        result = True
        msg = ""
        try:
            # 시간 순으로 정렬
            raw_df=self.raw_df
            sorted_raw_df=raw_df.sort_values(by='datetime')
            
            # print(sorted_raw_df.head(30))
            
            coordinate=sorted_raw_df['coordinate']
            coordinate.dropna(inplace=True)
            
            # X, Y 좌표 분리
            x, y = [], []
            for value in coordinate.values:
                x.append(float(value[0]))
                y.append(float(value[1]))
                
            # 시작 시간, 종료 시간 분리
            raw_time=sorted_raw_df['datetime'].values
            start_time, end_time = list(map(lambda x : datetime.strptime(x, DATETIME_FORMAT), raw_time[::2])), list(map(lambda x : datetime.strptime(x, DATETIME_FORMAT), raw_time[1::2]))
            time=np.array(end_time)-np.array(start_time)
            
            # 데이터 프레임 생성
            data_array=np.vstack([np.array(x), np.array(y), time, np.array(start_time)]).T
            df=pd.DataFrame(data_array, columns=['x_coordinate', 'y_coordinate', 'time', 'cycle_check'])
            
            # FOV 좌표값 -> FOV 이동거리로 변환 
            df['x_coordinate']=abs(df['x_coordinate'].diff()).astype(float)
            df['y_coordinate']=abs(df['y_coordinate'].diff()).astype(float)
            
            # TimeDelta 데이터 ms로 변환
            df['time']=df['time'].dt.total_seconds() * 1000
            # CycleTime check
            df['cycle_check'] = abs(df['cycle_check'].diff()).dt.total_seconds() * 1000
            
            # 쓰레기 값 제거 전 Shape
            # print(df.shape)
            # 1번째 쓰레기값 제거
            df.dropna(inplace=True)
            # 싸이클 5초 기준으로 체크 & 쓰레기값 제거
            df = df[df['cycle_check'] < 1000]
            # 싸이클 타임 데이터 제거
            df.drop(['cycle_check'], axis=1, inplace=True)
             # FOV 이동 시간 5초 이상 나는거 제거
            df = df[df['time'] < 5000]
            # Reset the index and drop the existing index
            df.reset_index(drop=True, inplace=True)
            # 쓰레기 값 제거 후 Shape
            # print(df.shape)
            # print(df.head(30))
            
            self.df=df
            
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                print(msg)
                
                
    def LinearRegressionModel(self):
        result = True
        msg = ""
        try:
            y_target = self.df['time']
            X_data = self.df.drop(['time'], axis=1, inplace=False)
            # Linear Regression 모델로 학습/예측/평가 수행. 
            lr = LinearRegression()
            lr.fit(X_data ,y_target )
            self.lr_model=lr
            
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                print(msg)
            
    def PolynomialRidgeModel(self):
        result = True
        msg = ""
        try:
            feature = self.df.drop(['time'], axis=1, inplace=False)
            target = self.df['time']
            
            # x_scaler=StandardScaler()
            # y_scaler=StandardScaler()
            
            # scaled_X_data=x_scaler.fit_transform(X_data)
            # scaled_y_data=y_scaler.fit_transform(y_target.values.reshape(-1, 1))
          
           
            # 로그 변환
            log_feature=np.log1p(feature)
            log_target=np.log1p(target)
    
            
            
            # Scaled Polynomial Ridge 모델로 학습/예측/평가 수행. 
            poly_model=Pipeline([('poly', PolynomialFeatures(degree=3, include_bias=False)), ('Ridge', Ridge(alpha=1))])
            poly_model.fit(log_feature, log_target)
            self.poly_model=poly_model
            
            # self.load_model(poly_model)
            # self.x_scaler=x_scaler
            # self.y_scaler=y_scaler
            
            # plt.show()
            
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                print(msg)
                
    def treeModel(self):
        result = True
        msg = ""
        try:
            feature = self.df.drop(['time'], axis=1, inplace=False)
            target = self.df['time']
            
            # x_scaler=StandardScaler()
            # y_scaler=StandardScaler()
            
            # scaled_X_data=x_scaler.fit_transform(X_data)
            # scaled_y_data=y_scaler.fit_transform(y_target.values.reshape(-1, 1))
          
           
            # 로그 변환
            log_feature=np.log1p(feature)
            log_target=np.log1p(target)
    
            
            
            # Scaled Polynomial Ridge 모델로 학습/예측/평가 수행. 
            # poly_model=Pipeline([('poly', PolynomialFeatures(degree=3, include_bias=False)), ('Ridge', Ridge(alpha=1))])
            # poly_model.fit(log_feature, log_target)
            treemodel=XGBRegressor(objective='reg:squarederror', n_estimators=400, learning_rate=0.05, max_depth=3)
            treemodel.fit(log_feature, log_target)
            self.poly_model=treemodel
            
            self.load_model(treemodel)
            # self.x_scaler=x_scaler
            # self.y_scaler=y_scaler
            
            # plt.show()
            
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                print(msg)
            
    def load_model(self, model):
        result = True
        msg = ""
        try:
            joblib.dump(model, './db/model.pkl')
        except Exception as ex:
            result = False
            msg = "{}".format(traceback.format_exc())
        finally:
            if result == False:
                print(msg)
            
            

        
        
        