<template>
  <div id="app">
    <!-- 背景容器 -->
    <div class="background-container">
      <!-- 左侧内容 -->
      <div class="left-panel">
        <h1 class="system-title">Smart Sign Language Translation System</h1>
        <p class="system-description">
          This system achieves a real-time, contactless and robust "sign-to-speech" functionality, by integrating a high-performance polymer-based pyroelectric sensor array and artificial intelligence. It distinguishes multiple words, phrases and continuous sentences, similar signs with identical hand gestures but different body expressions, and operates reliably in both bright and dark conditions.
        </p>
      </div>
      <!-- 右侧内容 -->
      <div class="right-panel">
        <div v-if="currentMapping" class="prediction-container">
          <p class="prediction-text">{{ currentMapping.text }}</p>
          <img :src="currentMapping.image" alt="Prediction" class="prediction-image">
        </div>
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
      currentMapping: null, // 存储后端返回的预测结果
      mappings: {
        // 7: {
        //   text: "What",
        //   image: require("./assets/pictures/what.png"),
        //   sound: require("./assets/sounds/what.mp3"),
        // },
        // 8: {
        //   text: "Can",
        //   image: require("./assets/pictures/can.png"),
        //   sound: require("./assets/sounds/can.mp3"),
        // },
        // 9: {
        //   text: "We",
        //   image: require("./assets/pictures/we.png"),
        //   sound: require("./assets/sounds/we.mp3"),
        // },
        // 10: {
        //   text: "Help",
        //   image: require("./assets/pictures/help.png"),
        //   sound: require("./assets/sounds/help.mp3"),
        // },
        // 11: {
        //   text: "You",
        //   image: require("./assets/pictures/you.png"),
        //   sound: require("./assets/sounds/you.mp3"),
        // },
        0: {
          text: "Know",
          image: require("./assets/pictures/know.png"),
          sound: require("./assets/sounds/know.mp3"),
        },
        1: {
          text: "Don't Know",
          image: require("./assets/pictures/dontknow.png"),
          sound: require("./assets/sounds/dontknow.mp3"),
        },
        2: {
          text: "I",
          image: require("./assets/pictures/I.png"),
          sound: require("./assets/sounds/I.mp3"),
        },
        3: {
          text: "You",
          image: require("./assets/pictures/you.png"),
          sound: require("./assets/sounds/you.mp3"),
        },
      }
    };
  },
  mounted() {
    window.addEventListener('keydown', this.handleKeyDown);
  },
  beforeUnmount() {
    window.removeEventListener('keydown', this.handleKeyDown);
  },
  methods: {
    async fetchPrediction() {
      try {
      // 向后端发送 GET 请求，无需传递参数
        const response = await axios.get('http://localhost:8000/predict');
      // const response = api.getContent({...})
        console.log('请求成功:', response.data);
      // 更新结果
        const number = response.data.prediction[0];
        this.currentMapping = this.mappings[number];
        this.$forceUpdate();
        this.playSound();
        console.log('currentMapping:', this.currentMapping);
      } catch (error) {
        console.error('请求失败:', error);
        alert('请求失败，请检查后端服务是否运行正常！');
      }
    },
    playSound() {
      if (this.currentMapping && this.currentMapping.sound) {
        const audio = new Audio(this.currentMapping.sound);
        audio.play()
            .catch(error => {
              console.error("声音播放失败:", error);
              alert("声音播放被浏览器阻止，请允许自动播放或检查文件路径！");
            });
      }
    },
    handleKeyDown(event) {
    // 检测空格键（keyCode 32）
      if (event.keyCode === 32) {
        this.fetchPrediction();
      }
    },
  },
};
</script>

<style>
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
/* 新增布局样式 */
.background-container {
  /* 保持原有背景设置 */
  /*background-image: url('./assets/background.png');*/
  background-color: #ffffff;
  /*background-size: cover;*/
  /*background-position: center;*/
  height: 100%;
  display: flex;
  flex-direction: row; /* 改为横向布局 */
}

.left-panel {
  flex: 1; /* 占据左侧50%空间 */
  padding: 40px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.right-panel {
  flex: 1; /* 占据右侧50%空间 */
  display: flex;
  align-items: center;
  justify-content: center;
}

.system-title {
  font-size: 3em;
  color: #000000FF;
  text-align: center;
  margin-bottom: 20px;
  font-weight: bold;
}
.system-description {
  font-size: 2em;
  color: #000000FF;
  text-align: center;
  line-height: 1.6;
  font-weight: bold;
}
.prediction-container {
  text-align: center;
}
.prediction-text {
  font-size: 4em;
  color: #000000FF;
  margin-bottom: 20px;
}
.prediction-image {
  width: 600px;
  height: auto;
}
</style>