from typing import Union
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import numpy as np
import serial
import serial.tools.list_ports
import re
import pandas as pd

@asynccontextmanager
async def lifespan(app: FastAPI):
    global knn_model
    knn_model = joblib.load("knn_model_7to11.joblib")
    print("Model loaded successfully!")
    # global df
    # df = pd.read_excel('./data/signdata.xlsx', header=None)
    yield
    knn_model = None

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  # 允许的前端地址
    allow_credentials=True,                  # 是否允许携带 Cookie
    allow_methods=["*"],                     # 允许的 HTTP 方法
    allow_headers=["*"],                     # 允许的请求头
)

@app.get("/predict")
def predict():
    try:
        ports_list = list(serial.tools.list_ports.comports())
        if len(ports_list) <= 0:
            print("无串口设备。")
        else:
            print("可用的串口设备如下：")
            for comport in ports_list:
                print(list(comport)[0], list(comport)[1])

            ser = serial.Serial("COM3", 115200)  # 打开COM17，将波特率配置为115200，其余参数使用默认值
            if ser.isOpen():  # 判断串口是否成功打开
                print("打开串口成功。")
                print(ser.name)  # 输出串口号
            else:
                print("打开串口失败。")

        array = []
        while True:
            com_input = ser.readline()
            LL = len(array)
            if com_input and LL <= 900:
                com_input = str(com_input, 'utf-8')
                a = re.findall("\\d+\\.?\\d*", com_input)  # 提取数字（包括整数和浮点数）
                a = list(map(int, a))  # 转换为整数
                array.extend(a)
            else:
                print(array)
                ser.close()
                if not ser.isOpen():
                    print("串口已关闭。")
                    break

        print(len(array))
        array = array[1:900]

        # 将用户输入的数据转换为 NumPy 数组
        input_data = np.array(array).reshape(1, -1)

        # 使用加载的模型进行预测
        prediction = knn_model.predict(input_data)

        # 返回预测结果
        return {"message": "success", "prediction": prediction.tolist()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during prediction: {str(e)}")

@app.get("/test")
def test():
    import random
    random_number = []
    random_number.append(random.randint(7, 11))
    print(random_number)
    return {"message": "success", "prediction": random_number}

# class PredictionRequest(BaseModel):
#     data: int
#
# @app.post("/predict")
# def predict(request: PredictionRequest):
#     try:
#         print(request.data)
#         data = np.array(df)
#         column = data.shape[1]
#         X = data[request.data, 0:column - 1]
#         prediction = knn_model.predict(X.reshape(1, -1))
#         # input_data = np.array(request.data).reshape(1, -1)
#         # prediction = knn_model.predict(input_data)
#         # 返回预测结果
#         return {"message": "success", "prediction": prediction.tolist()}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error during prediction: {str(e)}")


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app='main:app', host="0.0.0.0", port=8000, reload=True)