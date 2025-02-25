from typing import Union
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import numpy as np

@asynccontextmanager
async def lifespan(app: FastAPI):
    global knn_model
    knn_model = joblib.load("knn_model.joblib")
    print("Model loaded successfully!")
    import pandas as pd
    global df
    df = pd.read_excel('./data/signdata.xlsx', header=None)
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

# class PredictionRequest(BaseModel):
#     data: list

# @app.post("/predict")
# def predict(request: PredictionRequest):
#     try:
#         # 将用户输入的数据转换为 NumPy 数组
#         input_data = np.array(request.data).reshape(1, -1)
#
#         # 使用加载的模型进行预测
#         prediction = knn_model.predict(input_data)
#
#         # 返回预测结果
#         return {"prediction": prediction.tolist()}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error during prediction: {str(e)}")

class PredictionRequest(BaseModel):
    data: int

@app.post("/predict")
def predict(request: PredictionRequest):
    try:
        print(request.data)
        data = np.array(df)
        column = data.shape[1]
        X = data[request.data, 0:column - 1]
        prediction = knn_model.predict(X.reshape(1, -1))
        # input_data = np.array(request.data).reshape(1, -1)
        # prediction = knn_model.predict(input_data)
        # 返回预测结果
        return {"message": "success", "prediction": prediction.tolist()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during prediction: {str(e)}")


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app='main:app', host="0.0.0.0", port=8000, reload=True)