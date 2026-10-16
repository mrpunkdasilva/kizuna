<template>
  <section class="dashboard">
    <div class="dash-header">
      <div>
        <h2>Minhas Vagas</h2>
        <p class="dash-sub">{{ jobs.length }} vaga(s) salva(s)</p>
      </div>
      <div class="dash-tools">
        <input
          v-model="search"
          type="text"
          placeholder="Buscar por título, empresa ou local..."
        />
        <button class="btn-refresh" @click="fetchJobs" :disabled="loading">
          <span v-if="loading">Carregando...</span>
          <span v-else>Atualizar</span>
        </button>
      </div>
    </div>

    <div v-if="error" class="error-msg">{{ error }}</div>

    <div v-if="loading && !jobs.length" class="dash-state">
      <span class="spinner"></span>
      <span>Buscando suas vagas salvas...</span>
    </div>

    <div v-else-if="!filteredJobs.length" class="dash-state empty">
      <p class="empty-title">
        {{ jobs.length ? 'Nenhuma vaga corresponde à busca.' : 'Nenhuma vaga salva ainda.' }}
      </p>
      <p v-if="!jobs.length" class="dim">
        Analise uma vaga na aba <strong>Analisar Vaga</strong> e clique em
        <strong>Salvar Vaga</strong> para vê-la aqui.
      </p>
    </div>

    <div v-else class="jobs-grid">
      <article
        v-for="job in filteredJobs"
        :key="job.id"
        class="job-card"
        @click="openJob(job)"
      >
        <div class="job-card-head">
          <h3>{{ text(job.title) || 'Vaga sem título' }}</h3>
          <span v-if="text(job.compatibility_score)" class="match">
            {{ text(job.compatibility_score) }}
          </span>
        </div>

        <p class="company">{{ text(job.company) || 'Empresa não informada' }}</p>

        <div v-if="badges(job).length" class="badges">
          <span v-for="badge in badges(job)" :key="badge" class="badge">
            {{ badge }}
          </span>
        </div>

        <div v-if="array(job.tech_stack).length" class="techs">
          <span
            v-for="tech in array(job.tech_stack).slice(0, 5)"
            :key="tech"
            class="tech"
          >
            {{ tech }}
          </span>
        </div>

        <footer class="job-card-foot">
          <span class="date">{{ formatDate(job.createdAt) }}</span>
          <button class="btn-del" @click.stop="deleteJob(job)">Excluir</button>
        </footer>
      </article>
    </div>

    <transition name="fade">
      <div v-if="selectedJob" class="modal-overlay" @click.self="selectedJob = null">
        <div class="modal">
          <button class="modal-close" @click="selectedJob = null">×</button>

          <header class="modal-head">
            <h2>{{ text(selectedJob.title) || 'Vaga sem título' }}</h2>
            <h3>{{ text(selectedJob.company) || 'Empresa não informada' }}</h3>
            <div v-if="badges(selectedJob).length" class="badges">
              <span v-for="badge in badges(selectedJob)" :key="badge" class="badge">
                {{ badge }}
              </span>
              <span v-if="text(selectedJob.compatibility_score)" class="badge primary">
                Match: {{ text(selectedJob.compatibility_score) }}
              </span>
            </div>
          </header>

          <div class="modal-body">
            <div v-if="array(selectedJob.tech_stack).length" class="modal-section">
              <h4><i class="icon">🚀</i> Tech Stack</h4>
              <ul>
                <li v-for="tech in array(selectedJob.tech_stack)" :key="tech">{{ tech }}</li>
              </ul>
            </div>

            <div v-if="array(selectedJob.soft_skills).length" class="modal-section">
              <h4><i class="icon">🧠</i> Soft Skills</h4>
              <ul>
                <li v-for="skill in array(selectedJob.soft_skills)" :key="skill">{{ skill }}</li>
              </ul>
            </div>

            <div v-if="text(selectedJob.ai_summary)" class="modal-section highlight">
              <h4><i class="icon">✨</i> Kizuna's Insights</h4>
              <p>{{ text(selectedJob.ai_summary) }}</p>
            </div>

            <div v-if="array(selectedJob.requirements).length" class="modal-section">
              <h4><i class="icon">📋</i> Requisitos</h4>
              <ul>
                <li v-for="req in array(selectedJob.requirements)" :key="req">{{ req }}</li>
              </ul>
            </div>

            <div v-if="array(selectedJob.benefits).length" class="modal-section">
              <h4><i class="icon">🎁</i> Benefícios</h4>
              <ul>
                <li v-for="benefit in array(selectedJob.benefits)" :key="benefit">{{ benefit }}</li>
              </ul>
            </div>

            <div v-if="array(selectedJob.ats_keywords).length" class="modal-section">
              <h4><i class="icon">🔑</i> Palavras-chave (ATS)</h4>
              <div class="techs">
                <span v-for="kw in array(selectedJob.ats_keywords)" :key="kw" class="tech">
                  {{ kw }}
                </span>
              </div>
            </div>

            <div v-if="array(selectedJob.interview_tips).length" class="modal-section highlight-cyan">
              <h4><i class="icon">💡</i> Dicas para Entrevista</h4>
              <ul>
                <li v-for="tip in array(selectedJob.interview_tips)" :key="tip">{{ tip }}</li>
              </ul>
            </div>

            <div v-if="text(selectedJob.description)" class="modal-section">
              <h4><i class="icon">📝</i> Descrição</h4>
              <p class="description">{{ text(selectedJob.description) }}</p>
            </div>
          </div>

          <footer class="modal-foot">
            <a
              v-if="selectedJob.sourceUrl"
              :href="selectedJob.sourceUrl"
              target="_blank"
              rel="noopener"
              class="btn-source"
            >
              Ver vaga original
            </a>
            <button class="btn-copy" @click="copyInfo">
              {{ copied ? 'Copiado!' : 'Copiar Informações' }}
            </button>
            <button class="btn-del" @click="deleteJob(selectedJob)">Excluir Vaga</button>
          </footer>
        </div>
      </div>
    </transition>
  </section>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { logger } from '../utils/logger'

const API_BASE = 'http://localhost:8080'

const jobs = ref([])
const loading = ref(false)
const error = ref(null)
const search = ref('')
const selectedJob = ref(null)
const copied = ref(false)

const formatList = (value, inline = false) => {
  const items = array(value)
  if (!items.length) return 'Não informado'
  return inline ? items.join(', ') : items.map((item) => `• ${item}`).join('\n')
}

const copyInfo = async () => {
  if (!selectedJob.value) return
  const r = selectedJob.value

  const content = [
    `Vaga: ${text(r.title) || 'Não informado'}`,
    `Empresa: ${text(r.company) || 'Não informado'}`,
    `Local: ${text(r.location) || 'Não informado'}`,
    `Modelo: ${text(r.work_style) || 'Não informado'} | Tipo: ${text(r.employment_type) || 'Não informado'} | Senioridade: ${text(r.seniority) || 'Não informado'}`,
    `Salário: ${text(r.salary) || 'Não informado'}`,
    `Match: ${text(r.compatibility_score) || 'Não informado'}`,
    '',
    `Tech Stack: ${formatList(r.tech_stack, true)}`,
    `Soft Skills: ${formatList(r.soft_skills, true)}`,
    `Palavras-chave (ATS): ${formatList(r.ats_keywords, true)}`,
    '',
    `Resumo: ${text(r.ai_summary) || 'Não informado'}`,
    '',
    'Requisitos:',
    formatList(r.requirements),
    '',
    'Benefícios:',
    formatList(r.benefits),
    '',
    'Dicas de entrevista:',
    formatList(r.interview_tips),
    '',
    `Descrição: ${text(r.description) || 'Não informado'}`,
    '',
    `Fonte: ${r.sourceUrl || ''}`,
  ].join('\n')

  try {
    await navigator.clipboard.writeText(content)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
    logger.info('COPY_SUCCESS', { jobId: r.id })
  } catch (err) {
    logger.error('COPY_FAILURE', { error: err.message })
  }
}

const text = (value) => {
  if (value == null) return ''
  if (Array.isArray(value)) return value.filter(Boolean).join(', ')
  if (typeof value === 'object') return ''
  return String(value)
}

const array = (value) => {
  if (Array.isArray(value)) return value.filter((item) => item && item !== 'Não informado')
  if (value == null || value === '' || value === 'Não informado') return []
  if (typeof value === 'object') return []
  return [String(value)]
}

const badges = (job) =>
  [text(job.location), text(job.work_style), text(job.employment_type), text(job.seniority)]
    .filter((value) => value && value !== 'Não informado')

const formatDate = (value) => {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' })
}

const filteredJobs = computed(() => {
  const term = search.value.trim().toLowerCase()
  if (!term) return jobs.value
  return jobs.value.filter((job) =>
    [job.title, job.company, job.location]
      .map(text)
      .join(' ')
      .toLowerCase()
      .includes(term)
  )
})

const fetchJobs = async () => {
  loading.value = true
  error.value = null
  try {
    const { data } = await axios.get(`${API_BASE}/api/jobs`)
    jobs.value = Array.isArray(data) ? data : []
    logger.info('DASHBOARD_LOAD', { count: jobs.value.length })
  } catch (err) {
    error.value = 'Não foi possível carregar as vagas salvas. Tente novamente.'
    logger.error('DASHBOARD_FAILURE', { error: err.message })
  } finally {
    loading.value = false
  }
}

const openJob = (job) => {
  selectedJob.value = job
  logger.info('JOB_OPEN', { jobId: job.id })
}

const deleteJob = async (job) => {
  if (!job || !job.id) return
  if (!window.confirm(`Excluir a vaga "${text(job.title) || 'sem título'}"?`)) return

  try {
    await axios.delete(`${API_BASE}/api/jobs/${job.id}`)
    jobs.value = jobs.value.filter((item) => item.id !== job.id)
    if (selectedJob.value && selectedJob.value.id === job.id) {
      selectedJob.value = null
    }
    logger.info('JOB_DELETED', { jobId: job.id })
  } catch (err) {
    error.value = 'Não foi possível excluir a vaga. Tente novamente em instantes.'
    logger.error('JOB_DELETE_FAILURE', { jobId: job.id, error: err.message })
  }
}

onMounted(fetchJobs)
</script>

<style scoped>
.dashboard {
  margin-top: 20px;
}

.dash-header {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 30px;
}

.dash-header h2 {
  margin: 0;
  font-size: 1.8rem;
}

.dash-sub {
  margin: 6px 0 0;
  color: var(--text-dim);
  font-size: 0.9rem;
}

.dash-tools {
  display: flex;
  gap: 10px;
  flex: 1;
  min-width: 280px;
  justify-content: flex-end;
}

.dash-tools input {
  flex: 1;
  max-width: 360px;
  background: var(--card-bg);
  border: 1px solid #333;
  border-radius: 10px;
  padding: 12px 15px;
  color: white;
  font-size: 0.95rem;
  outline: none;
}

.dash-tools input:focus {
  border-color: var(--secondary);
}

.btn-refresh {
  background: linear-gradient(45deg, var(--primary), var(--secondary));
  border: none;
  padding: 0 24px;
  border-radius: 10px;
  color: #000;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.2s;
}

.btn-refresh:hover:not(:disabled) {
  transform: scale(1.05);
}

.btn-refresh:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.error-msg {
  margin-bottom: 20px;
  padding: 15px;
  background: rgba(255, 0, 0, 0.1);
  border-left: 4px solid #ff4444;
  color: #ff4444;
}

.dash-state {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 50px 20px;
  justify-content: center;
  color: var(--text-dim);
  background: var(--card-bg);
  border: 1px dashed #333;
  border-radius: 16px;
}

.dash-state.empty {
  flex-direction: column;
  text-align: center;
}

.empty-title {
  font-size: 1.1rem;
  color: var(--text);
  margin: 0;
}

.dash-state .dim {
  color: var(--text-dim);
  font-size: 0.9rem;
  margin: 8px 0 0;
}

.jobs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.job-card {
  background: var(--card-bg);
  border: 1px solid #333;
  border-radius: 16px;
  padding: 20px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 12px;
  transition: transform 0.2s, border-color 0.2s, box-shadow 0.2s;
}

.job-card:hover {
  transform: translateY(-4px);
  border-color: var(--primary);
  box-shadow: 0 12px 30px rgba(255, 0, 255, 0.15);
}

.job-card-head {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  justify-content: space-between;
}

.job-card-head h3 {
  margin: 0;
  font-size: 1.1rem;
  line-height: 1.3;
}

.match {
  flex: 0 0 auto;
  background: var(--primary);
  color: #fff;
  font-size: 0.75rem;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 999px;
  white-space: nowrap;
}

.company {
  margin: 0;
  color: var(--secondary);
  font-size: 0.95rem;
}

.badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.badge {
  background: #2a2a30;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.78rem;
  color: var(--text-dim);
}

.badge.primary {
  background: var(--primary);
  color: white;
  font-weight: 700;
}

.techs {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tech {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: var(--secondary);
  border: 1px solid rgba(0, 255, 255, 0.35);
  border-radius: 6px;
  padding: 2px 8px;
}

.job-card-foot {
  margin-top: auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 12px;
  border-top: 1px solid #2a2a30;
}

.date {
  font-size: 0.8rem;
  color: var(--text-dim);
}

.btn-del {
  background: transparent;
  border: 1px solid #ff4444;
  color: #ff4444;
  padding: 7px 14px;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}

.btn-del:hover {
  background: #ff4444;
  color: #000;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  z-index: 100;
}

.modal {
  position: relative;
  width: 100%;
  max-width: 760px;
  max-height: 90vh;
  overflow-y: auto;
  background: var(--card-bg);
  border: 1px solid #333;
  border-radius: 20px;
  padding: 30px;
  animation: slideUp 0.3s ease-out;
}

.modal-close {
  position: absolute;
  top: 16px;
  right: 20px;
  background: transparent;
  border: none;
  color: var(--text-dim);
  font-size: 2rem;
  line-height: 1;
  cursor: pointer;
  transition: color 0.2s;
}

.modal-close:hover {
  color: var(--primary);
}

.modal-head h2 {
  margin: 0;
  font-size: 1.8rem;
}

.modal-head h3 {
  margin: 5px 0 18px;
  color: var(--secondary);
  font-weight: 400;
}

.modal-body {
  display: flex;
  flex-direction: column;
  gap: 22px;
  margin: 25px 0;
}

.modal-section h4 {
  color: var(--text-dim);
  text-transform: uppercase;
  font-size: 0.8rem;
  letter-spacing: 1px;
  margin: 0 0 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.modal-section ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.modal-section li {
  padding: 5px 0;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.9rem;
}

.modal-section li::before {
  content: "»";
  color: var(--secondary);
  margin-right: 10px;
}

.modal-section p {
  line-height: 1.6;
  margin: 0;
}

.modal-section .description {
  white-space: pre-line;
  color: var(--text-dim);
}

.modal-section.highlight {
  background: rgba(255, 0, 255, 0.05);
  padding: 18px;
  border-radius: 12px;
  border: 1px dashed var(--primary);
}

.modal-section.highlight-cyan {
  background: rgba(0, 255, 255, 0.05);
  padding: 18px;
  border-radius: 12px;
  border: 1px dashed var(--secondary);
}

.modal-foot {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding-top: 20px;
  border-top: 1px solid #2a2a30;
}

.btn-source {
  background: var(--secondary);
  color: #000;
  text-decoration: none;
  padding: 10px 20px;
  border-radius: 8px;
  font-weight: 700;
  transition: transform 0.2s;
}

.btn-source:hover {
  transform: scale(1.05);
}

.btn-copy {
  background: transparent;
  border: 1px solid #444;
  color: var(--text-dim);
  padding: 10px 20px;
  border-radius: 8px;
  font-weight: 700;
  cursor: pointer;
  transition: border-color 0.2s, color 0.2s;
}

.btn-copy:hover {
  border-color: var(--secondary);
  color: var(--secondary);
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

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 600px) {
  .dash-tools {
    flex-direction: column;
  }
  .dash-tools input {
    max-width: none;
  }
  .btn-refresh {
    padding: 12px;
  }
}
</style>
