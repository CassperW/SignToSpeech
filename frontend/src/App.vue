<template>
  <div id="app">
    <!-- 背景容器 -->
    <div class="background-container">
      <!-- 输入框和按钮 -->
      <div class="center-box">
        <input
            type="number"
            v-model="inputValue"
            placeholder="请输入数字"
            class="input-field"
        />
        <button @click="fetchPrediction" class="submit-button">提交</button>
        <p v-if="result !== null">后端返回的预测结果：{{ result }}</p>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'App',
  data() {
    return {
      inputValue: '', // 绑定输入框的值
      result: null,   // 存储后端返回的预测结果
    };
  },
  methods: {
    async fetchPrediction() {
      try {
        const number = parseInt(this.inputValue, 10);
        if (isNaN(number)) {
          alert('请输入有效的数字！');
          return;
        }

        // 向后端发送请求
        const response = await axios.post('http://localhost:8000/predict', {
          data: number,
        });

        // 更新结果
        this.result = response.data.prediction[0];
      } catch (error) {
        console.error('请求失败:', error);
        alert('请求失败，请检查后端服务是否运行正常！');
      }
    },
  },
};
</script>

<style>
/* 全局样式 */
body, html {
  margin: 0;
  padding: 0;
  height: 100%;
  overflow: hidden;
}

#app {
  font-family: Arial, sans-serif;
  height: 100%;
}

/* 背景容器 */
.background-container {
  background-image: url('./assets/background.png'); /* 替换为你的背景图片路径 */
  background-size: cover;
  background-position: center;
  height: 100%;
  display: flex;
  justify-content: center; /* 水平居中 */
  align-items: center;     /* 垂直居中 */
}

/* 中间内容样式 */
.center-box {
  text-align: center;
  background: rgba(255, 255, 255, 0.8); /* 半透明背景 */
  padding: 20px;
  border-radius: 10px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

/* 输入框样式 */
.input-field {
  padding: 10px;
  font-size: 16px;
  width: 200px;
  margin-bottom: 10px;
  border: 1px solid #ccc;
  border-radius: 5px;
}

/* 按钮样式 */
.submit-button {
  padding: 10px 20px;
  font-size: 16px;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}

.submit-button:hover {
  background-color: #369f6e;
}

/* 结果文本样式 */
p {
  margin-top: 10px;
  font-size: 18px;
  color: #333;
}
</style>