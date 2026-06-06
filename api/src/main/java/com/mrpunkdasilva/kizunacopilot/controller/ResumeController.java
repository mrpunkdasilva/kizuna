package com.mrpunkdasilva.kizunacopilot.controller;

import com.mrpunkdasilva.kizunacopilot.service.PdfService;
import io.micrometer.core.instrument.MeterRegistry;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

@RestController
@RequestMapping("/api/resume")
@Slf4j
public class ResumeController {

    private final PdfService pdfService;
    private final MeterRegistry meterRegistry;

    public ResumeController(PdfService pdfService, MeterRegistry meterRegistry) {
        this.pdfService = pdfService;
        this.meterRegistry = meterRegistry;
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
