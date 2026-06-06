const APP_NAME = 'kizuna-copilot-client';

const log = (level, event, data = {}) => {
  const timestamp = new Date().toISOString();
  const logMessage = {
    timestamp,
    level,
    app: APP_NAME,
    event,
    ...data
  };
  
  if (level === 'ERROR') {
    console.error(`[${timestamp}] ${level} - ${event}`, data);
  } else {
    console.log(`[${timestamp}] ${level} - ${event}`, data);
  }
  
  // Aqui poderíamos enviar para um coletor de logs como Loki ou Elastic
};

export const logger = {
  info: (event, data) => log('INFO', event, data),
  warn: (event, data) => log('WARN', event, data),
  error: (event, data) => log('ERROR', event, data),
};
