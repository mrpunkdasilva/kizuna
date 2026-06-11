package com.mrpunkdasilva.kizunacopilot.controller;

import com.mrpunkdasilva.kizunacopilot.repository.JobPostingRepository;
import com.mrpunkdasilva.kizunacopilot.service.PdfService;
import com.mrpunkdasilva.kizunacopilot.service.ResumeService;
import io.micrometer.core.instrument.MeterRegistry;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

import java.net.MalformedURLException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

@RestController
@RequestMapping("/api/resume")
@Slf4j
public class ResumeController {

    private final PdfService pdfService;
    private final ResumeService resumeService;
    private final JobPostingRepository jobPostingRepository;
    private final MeterRegistry meterRegistry;

    public ResumeController(PdfService pdfService, ResumeService resumeService, 
                            JobPostingRepository jobPostingRepository, MeterRegistry meterRegistry) {
        this.pdfService = pdfService;
        this.resumeService = resumeService;
        this.jobPostingRepository = jobPostingRepository;
        this.meterRegistry = meterRegistry;
    }

    @GetMapping("/download/{fileName}")
    public ResponseEntity<Resource> downloadPdf(@PathVariable String fileName) {
        try {
            Path path = Paths.get("output", fileName);
            Resource resource = new UrlResource(path.toUri());

            if (resource.exists() || resource.isReadable()) {
                return ResponseEntity.ok()
                        .contentType(MediaType.APPLICATION_PDF)
                        .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"" + fileName + "\"")
                        .body(resource);
            } else {
                return ResponseEntity.notFound().build();
            }
        } catch (MalformedURLException e) {
            log.error("Error creating resource for file: {}", fileName, e);
            return ResponseEntity.internalServerError().build();
        }
    }

    @PostMapping("/tailor/{jobId}")
    public Mono<ResponseEntity<String>> tailorResume(@PathVariable String jobId) {
        log.info("Event: RESUME_TAILOR_REQUEST, JobId: {}", jobId);
        meterRegistry.counter("kizuna.resume.tailor.requests").increment();

        return jobPostingRepository.findById(jobId)
                .flatMap(resumeService::createTailoredResume)
                .map(pdfFileName -> {
                    log.info("Event: RESUME_TAILOR_SUCCESS, File: {}", pdfFileName);
                    return ResponseEntity.ok(pdfFileName);
                })
                .defaultIfEmpty(ResponseEntity.notFound().build())
                .onErrorResume(e -> {
                    log.error("Event: RESUME_TAILOR_ERROR, JobId: {}, Error: {}", jobId, e.getMessage());
                    return Mono.just(ResponseEntity.internalServerError().body(e.getMessage()));
                });
    }

    @PostMapping("/pdf")
    public ResponseEntity<String> generatePdf(@RequestParam String fileName) {
        log.info("Event: PDF_GEN_REQUEST, File: {}, App: kizuna-copilot", fileName);
        meterRegistry.counter("kizuna.pdf.requests", "file", fileName).increment();
        
        try {
            // Paths are relative to the project root
            Path mdPath = Paths.get("curriculums", fileName);
            if (!Files.exists(mdPath)) {
                log.warn("Event: PDF_GEN_FILE_NOT_FOUND, File: {}", fileName);
                return ResponseEntity.badRequest().body("File not found: " + mdPath.toString());
            }

            String markdownContent = Files.readString(mdPath);
            String pdfFileName = fileName.replace(".md", ".pdf");
            Path outputPath = Paths.get("output", pdfFileName);

            // Ensure output directory exists
            Files.createDirectories(outputPath.getParent());

            pdfService.generatePdfFromMarkdown(markdownContent, outputPath.toString());

            log.info("Event: PDF_GEN_SUCCESS, File: {}", pdfFileName);
            meterRegistry.counter("kizuna.pdf.success").increment();

            return ResponseEntity.ok("PDF generated successfully: " + outputPath.toAbsolutePath().toString());
        } catch (Exception e) {
            log.error("Event: PDF_GEN_ERROR, File: {}, Error: {}", fileName, e.getMessage());
            meterRegistry.counter("kizuna.pdf.error").increment();
            return ResponseEntity.internalServerError().body("Error generating PDF: " + e.getMessage());
        }
    }
}
