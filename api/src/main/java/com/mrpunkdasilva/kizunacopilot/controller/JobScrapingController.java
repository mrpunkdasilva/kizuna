package com.mrpunkdasilva.kizunacopilot.controller;

import com.mrpunkdasilva.kizunacopilot.model.JobPosting;
import com.mrpunkdasilva.kizunacopilot.service.JobScrapingService;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Tag;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

import java.util.List;

@RestController
@RequestMapping("/api/jobs")
@Slf4j
public class JobScrapingController {

    private final JobScrapingService jobScrapingService;
    private final MeterRegistry meterRegistry;

    public JobScrapingController(JobScrapingService jobScrapingService, MeterRegistry meterRegistry) {
        this.jobScrapingService = jobScrapingService;
        this.meterRegistry = meterRegistry;
    }

    @PostMapping("/scrape")
    @ResponseStatus(HttpStatus.CREATED)
    public Mono<JobPosting> scrapeJobAndSave(@RequestBody ScrapeRequest request) {
        log.info("Event: SCRAPE_REQUEST, URL: {}, App: kizuna-copilot", request.getUrl());
        
        meterRegistry.counter("kizuna.scrape.requests", 
            List.of(Tag.of("url", request.getUrl()))).increment();

        return jobScrapingService.scrapeAndSaveJob(request.getUrl())
                .doOnSuccess(job -> {
                    log.info("Event: SCRAPE_SUCCESS, JobId: {}, Title: {}", job.getId(), job.getTitle());
                    meterRegistry.counter("kizuna.scrape.success").increment();
                })
                .doOnError(error -> {
                    log.error("Event: SCRAPE_ERROR, URL: {}, Error: {}", request.getUrl(), error.getMessage());
                    meterRegistry.counter("kizuna.scrape.error", "type", error.getClass().getSimpleName()).increment();
                });
    }

    @GetMapping("/hello")
    public Mono<String> hello() {
        return Mono.just("Hello from Kizuna Copilot Spring Boot Application!");
    }

    // Inner class for the request body
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    private static class ScrapeRequest {
        private String url;
    }
}
