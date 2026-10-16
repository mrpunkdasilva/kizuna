package com.mrpunkdasilva.kizunacopilot.controller;

import com.mrpunkdasilva.kizunacopilot.model.JobPosting;
import com.mrpunkdasilva.kizunacopilot.repository.JobPostingRepository;
import com.mrpunkdasilva.kizunacopilot.service.JobScrapingService;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Tag;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.BeanWrapper;
import org.springframework.beans.BeanWrapperImpl;
import org.springframework.data.domain.Sort;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.beans.PropertyDescriptor;
import java.util.List;

@RestController
@RequestMapping("/api/jobs")
@Slf4j
public class JobScrapingController {

    private final JobScrapingService jobScrapingService;
    private final JobPostingRepository jobPostingRepository;
    private final MeterRegistry meterRegistry;

    public JobScrapingController(JobScrapingService jobScrapingService, JobPostingRepository jobPostingRepository,
                                 MeterRegistry meterRegistry) {
        this.jobScrapingService = jobScrapingService;
        this.jobPostingRepository = jobPostingRepository;
        this.meterRegistry = meterRegistry;
    }

    @PostMapping("/scrape")
    @ResponseStatus(HttpStatus.ACCEPTED)
    public Mono<JobPosting> scrapeJob(@RequestBody ScrapeRequest request) {
        log.info("Event: SCRAPE_REQUEST, URL: {}, App: kizuna-copilot", request.getUrl());

        meterRegistry.counter("kizuna.scrape.requests", 
            List.of(Tag.of("url", request.getUrl()))).increment();

        return jobScrapingService.createPendingJob(request.getUrl())
                .doOnSuccess(job -> log.info("Event: SCRAPE_ACCEPTED, JobId: {}, URL: {}", job.getId(), request.getUrl()))
                .doOnError(error -> {
                    log.error("Event: SCRAPE_ENQUEUE_ERROR, URL: {}, Error: {}", request.getUrl(), error.getMessage());
                    meterRegistry.counter("kizuna.scrape.error", "type", error.getClass().getSimpleName()).increment();
                });
    }

    @PostMapping("/{id}/save")
    public Mono<ResponseEntity<JobPosting>> saveJob(@PathVariable String id) {
        log.info("Event: SAVE_JOB, JobId: {}", id);
        return jobScrapingService.saveJob(id)
                .map(saved -> {
                    log.info("Event: SAVE_JOB_SUCCESS, JobId: {}", saved.getId());
                    return ResponseEntity.ok(saved);
                })
                .defaultIfEmpty(ResponseEntity.notFound().build())
                .onErrorResume(IllegalStateException.class, error -> {
                    log.warn("Event: SAVE_JOB_CONFLICT, JobId: {}, Error: {}", id, error.getMessage());
                    return Mono.just(ResponseEntity.status(HttpStatus.CONFLICT).build());
                });
    }

    @GetMapping
    public Flux<JobPosting> listJobs() {
        log.info("Event: LIST_JOBS");
        return jobPostingRepository.findAll(Sort.by(Sort.Direction.DESC, "_id"));
    }

    @GetMapping("/{id}")
    public Mono<ResponseEntity<JobPosting>> getJobById(@PathVariable String id) {
        log.info("Event: GET_JOB, JobId: {}", id);
        return jobScrapingService.getJob(id)
                .map(ResponseEntity::ok)
                .defaultIfEmpty(ResponseEntity.notFound().build());
    }

    @PutMapping("/{id}")
    public Mono<ResponseEntity<JobPosting>> updateJob(@PathVariable String id, @RequestBody JobPosting update) {
        log.info("Event: UPDATE_JOB, JobId: {}", id);
        return jobPostingRepository.findById(id)
                .flatMap(existing -> {
                    copyNonNullProperties(update, existing);
                    return jobPostingRepository.save(existing);
                })
                .map(ResponseEntity::ok)
                .defaultIfEmpty(ResponseEntity.notFound().build());
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public Mono<Void> deleteJob(@PathVariable String id) {
        log.info("Event: DELETE_JOB, JobId: {}", id);
        return jobPostingRepository.deleteById(id);
    }

    @GetMapping("/hello")
    public Mono<String> hello() {
        return Mono.just("Hello from Kizuna Copilot Spring Boot Application!");
    }

    private void copyNonNullProperties(Object source, Object target) {
        BeanWrapper src = new BeanWrapperImpl(source);
        BeanWrapper trg = new BeanWrapperImpl(target);
        for (PropertyDescriptor pd : src.getPropertyDescriptors()) {
            String name = pd.getName();
            if ("id".equals(name) || "class".equals(name)) {
                continue;
            }
            Object value = src.getPropertyValue(name);
            if (value != null) {
                trg.setPropertyValue(name, value);
            }
        }
    }

    // Inner class for the request body
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    private static class ScrapeRequest {
        private String url;
    }
}
