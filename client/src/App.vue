<template>
  <div class="container">
    <header>
      <div class="logo">
        <span class="kizuna">Kizuna</span><span class="copilot">Copilot</span>
      </div>
      <p class="tagline">Sua guia de IA para conquistar a vaga dos sonhos.</p>
    </header>

    <main>
      <section class="search-box">
        <input 
          v-model="url" 
          type="text" 
          placeholder="Cole aqui a URL da vaga do LinkedIn..." 
          :disabled="loading"
          @keyup.enter="scrapeJob"
        />
        <button @click="scrapeJob" :disabled="loading || !url">
          <span v-if="loading">Analisando...</span>
          <span v-else>Scrape & Analyze</span>
        </button>
      </section>

      <div v-if="error" class="error-msg">
        {{ error }}
      </div>

      <transition name="fade">
        <div v-if="result" class="result-card">
          <div class="card-header">
            <h2>{{ result.title }}</h2>
            <h3>{{ result.company }}</h3>
            <div class="badge-container">
              <span class="badge">{{ result.location }}</span>
              <span class="badge" v-if="result.work_style">{{ result.work_style }}</span>
              <span class="badge primary" v-if="result.compatibility_score">Match: {{ result.compatibility_score }}</span>
            </div>
          </div>

          <div class="card-grid">
            <div class="grid-item">
              <h4><i class="icon">🚀</i> Tech Stack</h4>
              <ul>
                <li v-for="tech in result.tech_stack" :key="tech">{{ tech }}</li>
              </ul>
            </div>
            <div class="grid-item">
              <h4><i class="icon">🧠</i> Soft Skills</h4>
              <ul>
                <li v-for="skill in result.soft_skills" :key="skill">{{ skill }}</li>
              </ul>
            </div>
          </div>

          <div class="ai-summary">
            <h4><i class="icon">✨</i> Kizuna's Insights</h4>
            <p>{{ result.ai_summary }}</p>
          </div>

          <div class="tips-box">
            <h4><i class="icon">💡</i> Dicas para Entrevista</h4>
            <ul>
              <li v-for="tip in result.interview_tips" :key="tip">{{ tip }}</li>
            </ul>
          </div>
        </div>
      </transition>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { logger } from './utils/logger'

const url = ref('')
const loading = ref(false)
const result = ref(null)
const error = ref(null)

const scrapeJob = async () => {
  if (!url.value) return
  
  loading.value = true
  result.value = null
  error.value = null

  logger.info('SCRAPE_START', { url: url.value })

  try {
    const response = await axios.post('http://localhost:8080/api/jobs/scrape', {
      url: url.value
    })
    result.value = response.data
    logger.info('SCRAPE_SUCCESS', { jobId: result.value.id, title: result.value.title })
  } catch (err) {
    logger.error('SCRAPE_FAILURE', { url: url.value, error: err.message })
    error.value = 'Ops! Algo deu errado ao analisar a vaga. Verifique a URL e tente novamente.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.container {
  max-width: 900px;
  margin: 0 auto;
  padding: 40px 20px;
}

header {
  text-align: center;
  margin-bottom: 50px;
}

.logo {
  font-size: 3rem;
  font-weight: 800;
  letter-spacing: -1px;
}

.kizuna { color: var(--primary); }
.copilot { color: var(--secondary); }

.tagline {
  color: var(--text-dim);
  font-size: 1.1rem;
  margin-top: 10px;
}

.search-box {
  display: flex;
  gap: 10px;
  background: var(--card-bg);
  padding: 10px;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.5);
  border: 1px solid #333;
}

input {
  flex: 1;
  background: transparent;
  border: none;
  padding: 15px;
  color: white;
  font-size: 1rem;
  outline: none;
}

button {
  background: linear-gradient(45deg, var(--primary), var(--secondary));
  border: none;
  padding: 0 30px;
  border-radius: 8px;
  color: #000;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.2s;
}

button:hover:not(:disabled) {
  transform: scale(1.05);
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.error-msg {
  margin-top: 20px;
  padding: 15px;
  background: rgba(255, 0, 0, 0.1);
  border-left: 4px solid #ff4444;
  color: #ff4444;
}

.result-card {
  margin-top: 40px;
  background: var(--card-bg);
  border-radius: 20px;
  padding: 30px;
  border: 1px solid #333;
  animation: slideUp 0.5s ease-out;
}

.card-header h2 {
  margin: 0;
  font-size: 2rem;
}

.card-header h3 {
  margin: 5px 0 20px;
  color: var(--secondary);
  font-weight: 400;
}

.badge-container {
  display: flex;
  gap: 10px;
  margin-bottom: 30px;
}

.badge {
  background: #2a2a30;
  padding: 5px 15px;
  border-radius: 20px;
  font-size: 0.85rem;
  color: var(--text-dim);
}

.badge.primary {
  background: var(--primary);
  color: white;
  font-weight: 700;
}

.card-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30px;
  margin-bottom: 30px;
}

h4 {
  color: var(--text-dim);
  text-transform: uppercase;
  font-size: 0.8rem;
  letter-spacing: 1px;
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  gap: 8px;
}

ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

li {
  padding: 5px 0;
  color: var(--text);
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.9rem;
}

li::before {
  content: "»";
  color: var(--secondary);
  margin-right: 10px;
}

.ai-summary {
  background: rgba(255, 0, 255, 0.05);
  padding: 20px;
  border-radius: 12px;
  border: 1px dashed var(--primary);
  margin-bottom: 30px;
}

.ai-summary p {
  line-height: 1.6;
}

.tips-box {
  background: rgba(0, 255, 255, 0.05);
  padding: 20px;
  border-radius: 12px;
  border: 1px dashed var(--secondary);
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.5s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
