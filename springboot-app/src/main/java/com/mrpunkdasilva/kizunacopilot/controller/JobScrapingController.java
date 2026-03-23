package com.mrpunkdasilva.kizunacopilot.controller;

import com.mrpunkdasilva.kizunacopilot.model.JobPosting;
import com.mrpunkdasilva.kizunacopilot.service.JobScrapingService;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

@RestController
@RequestMapping("/api/jobs")
@RequiredArgsConstructor
@Slf4j
public class JobScrapingController {

    private final JobScrapingService jobScrapingService;

    @PostMapping("/scrape")
    @ResponseStatus(HttpStatus.CREATED)
    public Mono<JobPosting> scrapeJobAndSave(@RequestBody ScrapeRequest request) {
        log.info("Received request to scrape job: {}", request.getUrl());
        return jobScrapingService.scrapeAndSaveJob(request.getUrl());
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
