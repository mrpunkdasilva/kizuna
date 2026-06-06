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

@Service
@Slf4j
public class JobScrapingService {

    private final JobPostingRepository jobPostingRepository;
    private final WebClient webClient;

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

    public Mono<JobPosting> scrapeAndSaveJob(String jobUrl) {
        log.info("Scraping job URL: {}", jobUrl);
        log.info("Using Python Scraper Host: {}", pythonScraperHost);
        
        if (pythonScraperHost == null || pythonScraperHost.isEmpty()) {
            return Mono.error(new IllegalArgumentException("Python Scraper Host is not configured!"));
        }

        String fullUri = pythonScraperHost + "/scrape-job/";
        log.info("Full URI: {}", fullUri);
        
        return webClient.post()
                .uri(fullUri)
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(new ScraperRequest(jobUrl))
                .retrieve()
                .bodyToMono(JobPosting.class)
                .timeout(Duration.ofMinutes(10))
                .flatMap(scrapedJob -> {
                    log.info("Scraped Job successfully received");
                    if (scrapedJob != null) {
                        scrapedJob.setSourceUrl(jobUrl);
                        return jobPostingRepository.save(scrapedJob);
                    }
                    return Mono.empty();
                })
                .doOnError(e -> log.error("Error during scraping: {}", e.getMessage()));
    }

    @Data
    private static class ScraperRequest {
        private String url;
        public ScraperRequest(String url) {
            this.url = url;
        }
    }
}
