<template>
  <div class="container">
    <header class="topbar">
      <div class="logo">
        <span class="kizuna">Kizuna</span><span class="copilot">Copilot</span>
      </div>
      <nav class="menu">
        <button
          :class="{ active: view === 'analyze' }"
          @click="view = 'analyze'"
        >
          Analisar Vaga
        </button>
        <button
          :class="{ active: view === 'dashboard' }"
          @click="view = 'dashboard'"
        >
          Dashboard
        </button>
      </nav>
    </header>

    <p class="tagline">Sua guia de IA para conquistar a vaga dos sonhos.</p>

    <main>
      <template v-if="view === 'analyze'">
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

      <div v-if="loading" class="loading-panel">
        <div class="loading-head">
          <span class="spinner"></span>
          <span class="loading-text">{{ loadingMessage }}</span>
          <span class="loading-pct">{{ Math.round(progress) }}%</span>
        </div>
        <div class="progress-track">
          <div class="progress-fill" :style="{ width: progress + '%' }"></div>
        </div>
      </div>

      <div v-if="loading" class="result-card skeleton-card">
        <div class="card-header">
          <div class="sk sk-title"></div>
          <div class="sk sk-subtitle"></div>
          <div class="badge-container">
            <div class="sk sk-badge"></div>
            <div class="sk sk-badge"></div>
            <div class="sk sk-badge"></div>
          </div>
        </div>

        <div class="card-grid">
          <div class="grid-item" v-for="n in 2" :key="n">
            <div class="sk sk-heading"></div>
            <div class="sk sk-line"></div>
            <div class="sk sk-line short"></div>
            <div class="sk sk-line"></div>
          </div>
        </div>

        <div class="sk sk-block"></div>
        <div class="sk sk-block"></div>
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

          <div class="action-footer">
            <button @click="saveJob" :disabled="saving || saved" class="btn-save">
              <span v-if="saving">Salvando...</span>
              <span v-else-if="saved">Vaga Salva!</span>
              <span v-else>Salvar Vaga</span>
            </button>
            <button @click="copyInfo" class="btn-copy">
              {{ copied ? 'Copiado!' : 'Copiar Informações' }}
            </button>
            <button @click="tailorResume" :disabled="tailoring || pdfFile" class="btn-tailor">
              <span v-if="tailoring">Adaptando Currículo...</span>
              <span v-else-if="pdfFile">Currículo Adaptado!</span>
              <span v-else>Adaptar Meu Currículo para esta Vaga</span>
            </button>
            <a v-if="pdfFile" :href="'http://localhost:8080/api/resume/download/' + pdfFile" class="btn-download" target="_blank">
              Baixar PDF
            </a>
          </div>
        </div>
      </transition>
      </template>
      <JobsDashboard v-else />
    </main>
  </div>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'
import axios from 'axios'
import { logger } from './utils/logger'
import JobsDashboard from './components/JobsDashboard.vue'

const view = ref('analyze')
const url = ref('')
const loading = ref(false)
const tailoring = ref(false)
const result = ref(null)
const error = ref(null)
const pdfFile = ref(null)
const saving = ref(false)
const saved = ref(false)
const copied = ref(false)
const progress = ref(0)
const loadingMessage = ref('')
let pollTimer = null
let progressTimer = null
let progressStart = 0

const LOADING_STAGES = [
  { until: 18, message: 'Conectando à vaga...' },
  { until: 42, message: 'Lendo a descrição da vaga...' },
  { until: 70, message: 'Analisando os requisitos com a Kizuna...' },
  { until: 88, message: 'Montando o overview...' },
  { until: 100, message: 'Quase lá, finalizando...' },
]

const stopProgress = (completed = false) => {
  if (progressTimer) {
    clearInterval(progressTimer)
    progressTimer = null
  }
  if (completed) {
    progress.value = 100
    loadingMessage.value = 'Pronto!'
  }
}

const startProgress = () => {
  progressStart = Date.now()
  progress.value = 0
  loadingMessage.value = LOADING_STAGES[0].message
  stopProgress()
  progressTimer = setInterval(() => {
    const seconds = (Date.now() - progressStart) / 1000
    const estimate = 97 * (1 - Math.exp(-seconds / 35))
    progress.value = Math.max(progress.value, Math.min(97, estimate))
    const stage = LOADING_STAGES.find((s) => progress.value <= s.until) || LOADING_STAGES[LOADING_STAGES.length - 1]
    loadingMessage.value = stage.message
  }, 300)
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

const pollJob = (jobId) => {
  pollTimer = setInterval(async () => {
    try {
      const { data } = await axios.get(`http://localhost:8080/api/jobs/${jobId}`)

      if (data.status === 'COMPLETED') {
        stopPolling()
        stopProgress(true)
        result.value = data
        loading.value = false
        logger.info('SCRAPE_SUCCESS', { jobId, title: data.title })
      } else if (data.status === 'FAILED') {
        stopPolling()
        stopProgress()
        loading.value = false
        error.value = data.error || 'A Kizuna não conseguiu analisar essa vaga. Tente outra URL.'
        logger.error('SCRAPE_FAILED', { jobId, error: data.error })
      }
    } catch (err) {
      stopPolling()
      stopProgress()
      loading.value = false
      error.value = 'Houve um erro ao acompanhar o processamento da vaga.'
      logger.error('POLL_FAILURE', { jobId, error: err.message })
    }
  }, 3000)
}

const scrapeJob = async () => {
  if (!url.value) return

  stopPolling()
  loading.value = true
  result.value = null
  error.value = null
  pdfFile.value = null
  saved.value = false
  copied.value = false
  startProgress()

  logger.info('SCRAPE_START', { url: url.value })

  try {
    const response = await axios.post('http://localhost:8080/api/jobs/scrape', {
      url: url.value
    })
    const jobId = response.data.id
    logger.info('SCRAPE_ACCEPTED', { jobId })
    pollJob(jobId)
  } catch (err) {
    logger.error('SCRAPE_FAILURE', { url: url.value, error: err.message })
    error.value = 'Ops! Algo deu errado ao enviar a vaga. Verifique a URL e tente novamente.'
    stopProgress()
    loading.value = false
  }
}

onUnmounted(() => {
  stopPolling()
  stopProgress()
})

const tailorResume = async () => {
  if (!result.value || !result.value.id) return

  tailoring.value = true
  logger.info('TAILOR_START', { jobId: result.value.id })

  try {
    const response = await axios.post(`http://localhost:8080/api/resume/tailor/${result.value.id}`)
    pdfFile.value = response.data
    logger.info('TAILOR_SUCCESS', { file: pdfFile.value })
  } catch (err) {
    logger.error('TAILOR_FAILURE', { jobId: result.value.id, error: err.message })
    error.value = 'Houve um erro ao adaptar seu currículo. Tente novamente em instantes.'
  } finally {
    tailoring.value = false
  }
}

const formatList = (value, inline = false) => {
  if (Array.isArray(value)) {
    const items = value.filter((v) => v && v !== 'Não informado')
    if (!items.length) return 'Não informado'
    return inline ? items.join(', ') : items.map((v) => `• ${v}`).join('\n')
  }
  return value || 'Não informado'
}

const saveJob = async () => {
  if (!result.value || !result.value.id || saved.value) return

  saving.value = true
  logger.info('SAVE_START', { jobId: result.value.id })

  try {
    const { data } = await axios.post(`http://localhost:8080/api/jobs/${result.value.id}/save`)
    result.value = data
    saved.value = true
    logger.info('SAVE_SUCCESS', { jobId: data.id })
  } catch (err) {
    error.value = 'Não foi possível salvar a vaga. Tente novamente em instantes.'
    logger.error('SAVE_FAILURE', { jobId: result.value.id, error: err.message })
  } finally {
    saving.value = false
  }
}

const copyInfo = async () => {
  if (!result.value) return
  const r = result.value

  const text = [
    `Vaga: ${r.title || 'Não informado'}`,
    `Empresa: ${r.company || 'Não informado'}`,
    `Local: ${r.location || 'Não informado'}`,
    `Estilo: ${r.work_style || 'Não informado'} | Tipo: ${r.employment_type || 'Não informado'} | Nível: ${r.seniority || 'Não informado'}`,
    `Salário: ${r.salary || 'Não informado'}`,
    '',
    `Descrição: ${r.description || 'Não informado'}`,
    '',
    'Requisitos:',
    formatList(r.requirements),
    '',
    'Benefícios:',
    formatList(r.benefits),
    '',
    `Tech Stack: ${formatList(r.tech_stack, true)}`,
    `Soft Skills: ${formatList(r.soft_skills, true)}`,
    `Palavras-chave (ATS): ${formatList(r.ats_keywords, true)}`,
    `Compatibilidade: ${r.compatibility_score || 'Não informado'}`,
    '',
    `Resumo: ${r.ai_summary || 'Não informado'}`,
    '',
    'Dicas de entrevista:',
    formatList(r.interview_tips),
    '',
    `Fonte: ${r.sourceUrl || ''}`,
  ].join('\n')

  try {
    await navigator.clipboard.writeText(text)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
    logger.info('COPY_SUCCESS')
  } catch (err) {
    logger.error('COPY_FAILURE', { error: err.message })
  }
}
</script>

<style scoped>
/* ... (previous styles) ... */

.action-footer {
  margin-top: 30px;
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  justify-content: center;
}

.btn-save {
  background: var(--primary);
  color: #000;
  padding: 15px 30px;
  font-size: 1.1rem;
}

.btn-save:disabled {
  opacity: 0.6;
}

.btn-copy {
  background: transparent;
  color: var(--text-dim);
  border: 1px solid #444;
  padding: 15px 30px;
  font-size: 1.1rem;
}

.btn-copy:hover:not(:disabled) {
  border-color: var(--secondary);
  color: var(--secondary);
}

.btn-tailor {
  background: var(--secondary);
  color: black;
  padding: 15px 30px;
  font-size: 1.1rem;
}

.btn-download {
  background: var(--secondary);
  color: black;
  text-decoration: none;
  padding: 15px 30px;
  border-radius: 8px;
  font-weight: 700;
  display: flex;
  align-items: center;
  transition: transform 0.2s;
}

.btn-download:hover {
  transform: scale(1.05);
}

.container {
  max-width: 900px;
  margin: 0 auto;
  padding: 40px 20px;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 10px;
}

.logo {
  font-size: 3rem;
  font-weight: 800;
  letter-spacing: -1px;
}

.kizuna { color: var(--primary); }
.copilot { color: var(--secondary); }

.menu {
  display: flex;
  gap: 10px;
}

.menu button {
  background: transparent;
  border: 1px solid #333;
  color: var(--text-dim);
  padding: 10px 22px;
  border-radius: 10px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: border-color 0.2s, color 0.2s;
}

.menu button:hover:not(:disabled) {
  transform: none;
  border-color: var(--secondary);
  color: var(--secondary);
}

.menu button.active {
  background: linear-gradient(45deg, var(--primary), var(--secondary));
  border-color: transparent;
  color: #000;
}

.tagline {
  text-align: center;
  color: var(--text-dim);
  font-size: 1.1rem;
  margin-top: 10px;
  margin-bottom: 50px;
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

.loading-panel {
  margin-top: 30px;
  padding: 20px 24px;
  background: var(--card-bg);
  border: 1px solid #333;
  border-radius: 16px;
}

.loading-head {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--text-dim);
  font-size: 1rem;
}

.loading-text {
  flex: 1;
  transition: opacity 0.3s;
}

.loading-pct {
  font-variant-numeric: tabular-nums;
  font-weight: 700;
  color: var(--primary);
}

.progress-track {
  margin-top: 16px;
  height: 8px;
  border-radius: 999px;
  background: #1c1c22;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--primary), var(--secondary));
  transition: width 0.4s ease;
}

.spinner {
  width: 18px;
  height: 18px;
  flex: 0 0 auto;
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.skeleton-card {
  pointer-events: none;
  overflow: hidden;
}

.sk {
  position: relative;
  overflow: hidden;
  border-radius: 6px;
  background: #2a2a31;
}

.sk::after {
  content: "";
  position: absolute;
  inset: 0;
  transform: translateX(-100%);
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.07), transparent);
  animation: shimmer 1.4s ease-in-out infinite;
}

.sk-title { width: 60%; height: 28px; margin-bottom: 14px; }
.sk-subtitle { width: 35%; height: 18px; margin-bottom: 22px; }
.sk-badge { width: 90px; height: 26px; border-radius: 20px; }
.sk-heading { width: 45%; height: 12px; margin-bottom: 18px; }
.sk-line { height: 12px; margin: 12px 0; }
.sk-line.short { width: 60%; }
.sk-block { height: 90px; border-radius: 12px; margin-bottom: 30px; }

@keyframes shimmer {
  100% { transform: translateX(100%); }
}

@keyframes spin {
  to { transform: rotate(360deg); }
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

@media (max-width: 600px) {
  .topbar {
    flex-direction: column;
    align-items: stretch;
  }

  .logo {
    text-align: center;
  }

  .menu {
    justify-content: center;
  }
}
</style>
