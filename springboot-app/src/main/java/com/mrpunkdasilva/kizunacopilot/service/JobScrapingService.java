package com.mrpunkdasilva.kizunacopilot.service;

import com.mrpunkdasilva.kizunacopilot.model.JobPosting;
import com.mrpunkdasilva.kizunacopilot.repository.JobPostingRepository;
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

    private final WebClient webClient;
    private final JobPostingRepository jobPostingRepository;

    @Value("${python.scraper.host}")
    private String pythonScraperHost;

    public JobScrapingService(WebClient.Builder webClientBuilder, JobPostingRepository jobPostingRepository) {
        this.webClient = webClientBuilder.build();
        this.jobPostingRepository = jobPostingRepository;
    }

    public Mono<JobPosting> scrapeAndSaveJob(String jobUrl) {
        log.info("Scraping job URL: {}", jobUrl);
        // Assuming the Python scraper's /scrape-job/ endpoint accepts a JSON body with a 'url' field
        return webClient.post()
                .uri(pythonScraperHost + "/scrape-job/")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(new ScraperRequest(jobUrl))
                .retrieve()
                .bodyToMono(JobPosting.class)
                .timeout(Duration.ofSeconds(30)) // Increased timeout for scraping
                .flatMap(scrapedJob -> {
                    log.info("Scraped Job: {}", scrapedJob);
                    scrapedJob.setSourceUrl(jobUrl); // Set the original source URL
                    return jobPostingRepository.save(scrapedJob);
                })
                .doOnError(e -> log.error("Error during scraping or saving job: {}", e.getMessage()));
    }

    @Data
    private static class ScraperRequest {
        private String url;
        public ScraperRequest(String url) {
            this.url = url;
        }
    }
}
