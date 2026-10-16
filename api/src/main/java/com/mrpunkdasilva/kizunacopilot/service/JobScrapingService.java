package com.mrpunkdasilva.kizunacopilot.service;

import com.mrpunkdasilva.kizunacopilot.model.JobPosting;
import com.mrpunkdasilva.kizunacopilot.repository.JobPostingRepository;
import jakarta.annotation.PostConstruct;
import lombok.Data;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.time.Instant;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

@Service
@Slf4j
public class JobScrapingService {

    public static final String STATUS_PENDING = "PENDING";
    public static final String STATUS_COMPLETED = "COMPLETED";
    public static final String STATUS_FAILED = "FAILED";

    private final JobPostingRepository jobPostingRepository;
    private final WebClient webClient;

    /**
     * Holds analyzed jobs that were NOT yet persisted to MongoDB.
     * A job is only saved when the client explicitly requests it via {@link #saveJob(String)}.
     */
    private final Map<String, JobPosting> inMemoryJobs = new ConcurrentHashMap<>();

    @Value("${python.scraper.host}")
    private String pythonScraperHost;

    public JobScrapingService(JobPostingRepository jobPostingRepository, WebClient.Builder webClientBuilder) {
        this.jobPostingRepository = jobPostingRepository;
        this.webClient = webClientBuilder.build();
    }

    @PostConstruct
    public void init() {
        log.info("JobScrapingService initialized with Python Scraper Host: {}", pythonScraperHost);
    }

    /**
     * Creates an in-memory placeholder job (PENDING) and kicks off the scraping in the background.
     * Nothing is persisted to the database here.
     */
    public Mono<JobPosting> createPendingJob(String jobUrl) {
        log.info("Creating pending job (in-memory) for URL: {}", jobUrl);

        JobPosting pending = new JobPosting();
        pending.setId(UUID.randomUUID().toString());
        pending.setSourceUrl(jobUrl);
        pending.setStatus(STATUS_PENDING);
        pending.setCreatedAt(Instant.now());
        inMemoryJobs.put(pending.getId(), pending);

        processJobAsync(pending.getId(), jobUrl);
        return Mono.just(pending);
    }

    /**
     * Fire-and-forget processing. Result stays in memory until {@link #saveJob(String)} is called.
     */
    public void processJobAsync(String jobId, String jobUrl) {
        log.info("Event: SCRAPE_START, JobId: {}, URL: {}", jobId, jobUrl);

        fetchScrapedJob(jobUrl)
                .doOnNext(scraped -> {
                    scraped.setId(jobId);
                    scraped.setSourceUrl(jobUrl);
                    scraped.setCreatedAt(Instant.now());
                    scraped.setStatus(STATUS_COMPLETED);
                    scraped.setError(null);
                    inMemoryJobs.put(jobId, scraped);
                    log.info("Event: SCRAPE_SUCCESS, JobId: {}, Title: {}", jobId, scraped.getTitle());
                })
                .onErrorResume(error -> {
                    log.error("Event: SCRAPE_ERROR, JobId: {}, Error: {}", jobId, error.getMessage());
                    markFailed(jobId, error.getMessage());
                    return Mono.empty();
                })
                .subscribe();
    }

    private void markFailed(String jobId, String message) {
        JobPosting job = inMemoryJobs.get(jobId);
        if (job != null) {
            job.setStatus(STATUS_FAILED);
            job.setError(message);
            inMemoryJobs.put(jobId, job);
        }
    }

    /**
     * Looks up a job in memory first (not yet saved) and falls back to the database (already saved).
     */
    public Mono<JobPosting> getJob(String id) {
        JobPosting cached = inMemoryJobs.get(id);
        if (cached != null) {
            return Mono.just(cached);
        }
        return jobPostingRepository.findById(id);
    }

    /**
     * Persists a previously analyzed job to MongoDB. Removes it from memory on success.
     */
    public Mono<JobPosting> saveJob(String id) {
        JobPosting cached = inMemoryJobs.get(id);
        if (cached == null) {
            return jobPostingRepository.findById(id);
        }
        if (STATUS_PENDING.equals(cached.getStatus())) {
            return Mono.error(new IllegalStateException("A análise da vaga ainda não foi concluída."));
        }
        if (STATUS_FAILED.equals(cached.getStatus())) {
            return Mono.error(new IllegalStateException("Não é possível salvar uma análise que falhou."));
        }
        return jobPostingRepository.save(cached)
                .doOnSuccess(saved -> inMemoryJobs.remove(id));
    }

    private Mono<JobPosting> fetchScrapedJob(String jobUrl) {
        if (pythonScraperHost == null || pythonScraperHost.isEmpty()) {
            return Mono.error(new IllegalArgumentException("Python Scraper Host is not configured!"));
        }

        String fullUri = pythonScraperHost + "/scrape-job/";
        log.info("Calling Python scraper: {}", fullUri);

        return webClient.post()
                .uri(fullUri)
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(new ScraperRequest(jobUrl))
                .retrieve()
                .bodyToMono(JobPosting.class)
                .timeout(Duration.ofMinutes(10));
    }

    @Data
    private static class ScraperRequest {
        private String url;
        public ScraperRequest(String url) {
            this.url = url;
        }
    }
}
