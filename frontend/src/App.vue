<template>
  <div class="app-shell">
    <header class="topbar">
      <div>
        <p class="brand">SignToSpeech</p>
        <p class="model-name">1 m sensor model · 14 signs</p>
      </div>
      <div class="api-status" :class="{ online: apiOnline }">
        <span class="status-dot"></span>
        {{ apiOnline ? "Backend ready" : "Backend offline" }}
      </div>
    </header>

    <main class="workspace">
      <section class="control-panel" aria-labelledby="capture-title">
        <div class="section-heading">
          <div>
            <p class="eyebrow">LOCAL CAPTURE</p>
            <h1 id="capture-title">Sensor board</h1>
          </div>
          <Usb :size="30" aria-hidden="true" />
        </div>

        <div class="field-group">
          <div class="field-label-row">
            <label for="serial-port">Serial port</label>
            <button
              class="icon-button"
              type="button"
              title="Refresh serial ports"
              :disabled="isRefreshing || isPredicting"
              @click="refreshPorts"
            >
              <RefreshCw :size="18" :class="{ spinning: isRefreshing }" />
            </button>
          </div>

          <select
            id="serial-port"
            v-model="selectedPort"
            :disabled="isRefreshing || isPredicting || ports.length === 0"
          >
            <option value="" disabled>
              {{ ports.length ? "Select a device" : "No serial device" }}
            </option>
            <option v-for="port in ports" :key="port.device" :value="port.device">
              {{ port.device }} · {{ port.description }}
            </option>
          </select>
        </div>

        <div class="device-state">
          <component
            :is="selectedPort ? CheckCircle2 : AlertCircle"
            :size="20"
            aria-hidden="true"
          />
          <span>{{ deviceStatus }}</span>
        </div>

        <button
          class="capture-button"
          type="button"
          :disabled="!selectedPort || isPredicting"
          @click="capturePrediction"
        >
          <LoaderCircle v-if="isPredicting" :size="22" class="spinning" />
          <Radio v-else :size="22" />
          {{ isPredicting ? "Reading 1,025 sensors…" : "Start recognition" }}
        </button>

        <div v-if="errorMessage" class="error-message" role="alert">
          <AlertCircle :size="20" />
          <span>{{ errorMessage }}</span>
        </div>
      </section>

      <section class="result-panel" aria-live="polite">
        <div v-if="currentMapping" class="prediction-result">
          <p class="eyebrow">PREDICTION</p>
          <div class="result-visual">
            <img
              v-if="currentMapping.image"
              :src="currentMapping.image"
              :alt="currentMapping.text"
            />
            <Hand v-else :size="112" stroke-width="1.25" aria-hidden="true" />
          </div>
          <p class="prediction-text">{{ currentMapping.text }}</p>
          <p class="sample-count">1,025 sensor values · {{ lastPort }}</p>
        </div>

        <div v-else class="empty-result">
          <Hand :size="104" stroke-width="1.15" aria-hidden="true" />
          <p>Waiting for capture</p>
        </div>
      </section>
    </main>
  </div>
</template>

<script>
import axios from "axios";
import {
  AlertCircle,
  CheckCircle2,
  Hand,
  LoaderCircle,
  Radio,
  RefreshCw,
  Usb,
} from "lucide-vue-next";

const API_BASE_URL = process.env.VUE_APP_API_URL || "http://127.0.0.1:8000";

export default {
  name: "App",
  components: {
    AlertCircle,
    CheckCircle2,
    Hand,
    LoaderCircle,
    Radio,
    RefreshCw,
    Usb,
  },
  data() {
    return {
      apiOnline: false,
      ports: [],
      selectedPort: "",
      prediction: "",
      lastPort: "",
      errorMessage: "",
      isRefreshing: false,
      isPredicting: false,
      mappings: {
        Can: {
          text: "Can",
          image: require("./assets/pictures/can.png"),
          sound: require("./assets/sounds/can.mp3"),
        },
        DontKnow: {
          text: "Don't Know",
          image: require("./assets/pictures/dontknow.png"),
          sound: require("./assets/sounds/dontknow.mp3"),
        },
        Help: {
          text: "Help",
          image: require("./assets/pictures/help.png"),
          sound: require("./assets/sounds/help.mp3"),
        },
        I: {
          text: "I",
          image: require("./assets/pictures/I.png"),
          sound: require("./assets/sounds/I.mp3"),
        },
        Know: {
          text: "Know",
          image: require("./assets/pictures/know.png"),
          sound: require("./assets/sounds/know.mp3"),
        },
        What: {
          text: "What",
          image: require("./assets/pictures/what.png"),
          sound: require("./assets/sounds/what.mp3"),
        },
        You: {
          text: "You",
          image: require("./assets/pictures/you.png"),
          sound: require("./assets/sounds/you.mp3"),
        },
      },
    };
  },
  computed: {
    currentMapping() {
      if (!this.prediction) return null;
      return this.mappings[this.prediction] || {
        text: this.prediction,
        image: null,
        sound: null,
      };
    },
    deviceStatus() {
      if (this.selectedPort) return `${this.selectedPort} selected`;
      if (this.isRefreshing) return "Scanning serial ports";
      return this.ports.length ? "Device not selected" : "Device not detected";
    },
  },
  mounted() {
    this.refreshPorts();
    window.addEventListener("keydown", this.handleKeyDown);
  },
  beforeUnmount() {
    window.removeEventListener("keydown", this.handleKeyDown);
  },
  methods: {
    async refreshPorts() {
      this.isRefreshing = true;
      this.errorMessage = "";
      try {
        const response = await axios.get(`${API_BASE_URL}/ports`, { timeout: 4000 });
        this.ports = response.data;
        this.apiOnline = true;

        const selectedStillExists = this.ports.some(
          (port) => port.device === this.selectedPort
        );
        if (!selectedStillExists) {
          this.selectedPort = this.ports.length === 1 ? this.ports[0].device : "";
        }
      } catch (error) {
        this.apiOnline = false;
        this.ports = [];
        this.selectedPort = "";
        this.errorMessage = this.readError(error, "Cannot reach the local backend");
      } finally {
        this.isRefreshing = false;
      }
    },
    async capturePrediction() {
      if (!this.selectedPort || this.isPredicting) return;

      this.isPredicting = true;
      this.errorMessage = "";
      try {
        const response = await axios.post(
          `${API_BASE_URL}/capture-predict`,
          { port: this.selectedPort },
          { timeout: 15000 }
        );
        this.apiOnline = true;
        this.prediction = response.data.prediction;
        this.lastPort = response.data.port || this.selectedPort;
        this.playSound();
      } catch (error) {
        this.errorMessage = this.readError(error, "Recognition failed");
      } finally {
        this.isPredicting = false;
      }
    },
    playSound() {
      const sound = this.currentMapping?.sound;
      if (!sound) return;
      new Audio(sound).play().catch(() => {});
    },
    readError(error, fallback) {
      return error.response?.data?.detail || error.message || fallback;
    },
    handleKeyDown(event) {
      const tag = event.target?.tagName;
      if (event.code !== "Space" || tag === "SELECT" || tag === "INPUT") return;
      event.preventDefault();
      this.capturePrediction();
    },
  },
};
</script>

<style>
:root {
  color: #17201d;
  background: #f4f6f5;
  font-family: Inter, "Segoe UI", Arial, sans-serif;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  min-width: 320px;
  min-height: 100vh;
}

button,
select {
  font: inherit;
}

button:focus-visible,
select:focus-visible {
  outline: 3px solid rgba(24, 122, 88, 0.24);
  outline-offset: 2px;
}

.app-shell {
  min-height: 100vh;
  background: #f4f6f5;
}

.topbar {
  min-height: 88px;
  padding: 18px 36px;
  border-bottom: 1px solid #d7ddda;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}

.brand,
.model-name,
.eyebrow,
.prediction-text,
.sample-count,
.empty-result p {
  margin: 0;
}

.brand {
  font-size: 1.45rem;
  font-weight: 750;
}

.model-name {
  margin-top: 4px;
  color: #66716d;
  font-size: 0.88rem;
}

.api-status {
  min-width: 150px;
  color: #8b3e35;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 9px;
  font-size: 0.9rem;
  font-weight: 650;
}

.api-status.online {
  color: #176c4e;
}

.status-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: currentColor;
}

.workspace {
  min-height: calc(100vh - 88px);
  display: grid;
  grid-template-columns: minmax(320px, 440px) minmax(0, 1fr);
}

.control-panel {
  padding: 48px 42px;
  border-right: 1px solid #d7ddda;
  background: #ffffff;
}

.section-heading {
  margin-bottom: 48px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  color: #176c4e;
}

.eyebrow {
  color: #6b7672;
  font-size: 0.76rem;
  font-weight: 750;
}

h1 {
  margin: 8px 0 0;
  color: #17201d;
  font-size: 2rem;
  letter-spacing: 0;
}

.field-group {
  display: grid;
  gap: 10px;
}

.field-label-row {
  min-height: 36px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

label {
  font-size: 0.9rem;
  font-weight: 700;
}

.icon-button {
  width: 36px;
  height: 36px;
  padding: 0;
  border: 1px solid #ccd4d0;
  border-radius: 6px;
  color: #34413c;
  background: #ffffff;
  display: inline-grid;
  place-items: center;
  cursor: pointer;
}

.icon-button:hover:not(:disabled) {
  background: #edf2ef;
}

select {
  width: 100%;
  min-height: 48px;
  padding: 0 40px 0 13px;
  border: 1px solid #bfc9c4;
  border-radius: 6px;
  color: #17201d;
  background: #ffffff;
}

.device-state {
  min-height: 56px;
  margin: 18px 0 30px;
  padding: 13px 14px;
  border: 1px solid #d7ddda;
  border-radius: 6px;
  color: #55615c;
  background: #f7f9f8;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 0.9rem;
}

.capture-button {
  width: 100%;
  min-height: 52px;
  padding: 0 18px;
  border: 0;
  border-radius: 6px;
  color: #ffffff;
  background: #176c4e;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  font-weight: 750;
  cursor: pointer;
}

.capture-button:hover:not(:disabled) {
  background: #11563e;
}

button:disabled,
select:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.error-message {
  margin-top: 18px;
  padding: 13px 14px;
  border-left: 3px solid #b84f42;
  color: #7a332b;
  background: #fff4f2;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: 0.88rem;
  line-height: 1.45;
}

.result-panel {
  min-width: 0;
  padding: 42px;
  display: grid;
  place-items: center;
}

.prediction-result,
.empty-result {
  width: min(100%, 680px);
  text-align: center;
}

.result-visual {
  width: min(100%, 540px);
  aspect-ratio: 4 / 3;
  margin: 22px auto 26px;
  border: 1px solid #d7ddda;
  border-radius: 8px;
  color: #176c4e;
  background: #ffffff;
  display: grid;
  place-items: center;
  overflow: hidden;
}

.result-visual img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.prediction-text {
  font-size: 3.4rem;
  font-weight: 780;
}

.sample-count {
  margin-top: 10px;
  color: #6b7672;
  font-size: 0.9rem;
}

.empty-result {
  min-height: 360px;
  color: #8b9691;
  display: grid;
  place-content: center;
  gap: 22px;
}

.empty-result p {
  font-size: 1.1rem;
  font-weight: 650;
}

.spinning {
  animation: spin 0.9s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 760px) {
  .topbar {
    min-height: 76px;
    padding: 14px 20px;
  }

  .api-status {
    min-width: 0;
    font-size: 0;
  }

  .workspace {
    min-height: calc(100vh - 76px);
    grid-template-columns: 1fr;
  }

  .control-panel {
    padding: 30px 22px;
    border-right: 0;
    border-bottom: 1px solid #d7ddda;
  }

  .section-heading {
    margin-bottom: 30px;
  }

  .result-panel {
    min-height: 500px;
    padding: 30px 22px;
  }

  .prediction-text {
    font-size: 2.7rem;
  }
}
</style>
