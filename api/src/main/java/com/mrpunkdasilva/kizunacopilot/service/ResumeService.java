package com.mrpunkdasilva.kizunacopilot.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.mrpunkdasilva.kizunacopilot.model.JobPosting;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.Map;

@Service
@Slf4j
@RequiredArgsConstructor
public class ResumeService {

    private final OllamaService ollamaService;
    private final PdfService pdfService;
    private final ObjectMapper objectMapper;

    private static final String DATA_PATH = "data/";
    private static final String CURRICULUMS_PATH = "curriculums/";
    private static final String OUTPUT_PATH = "output/";

    public Mono<String> createTailoredResume(JobPosting job) {
        log.info("Creating tailored resume for job: {}", job.getTitle());

        return Mono.fromCallable(this::loadCandidateData)
                .flatMap(candidateData -> {
                    String prompt = buildTailorPrompt(candidateData, job);
                    return ollamaService.generateContent(prompt);
                })
                .flatMap(markdown -> saveAndExport(markdown, job));
    }

    private Map<String, Object> loadCandidateData() throws Exception {
        Map<String, Object> data = new HashMap<>();
        String[] files = {"informations.json", "summary.json", "experiences.json", "skills.json", "projects.json", "educations.json"};
        
        for (String file : files) {
            Path path = Paths.get(DATA_PATH, file);
            if (Files.exists(path)) {
                Object content = objectMapper.readValue(path.toFile(), Object.class);
                data.put(file.replace(".json", ""), content);
            }
        }
        return data;
    }

    private String buildTailorPrompt(Map<String, Object> candidateData, JobPosting job) {
        try {
            Path promptPath = Paths.get("kizuna-kokoro", "prompts", "tailor-resume.md");
            String template = Files.readString(promptPath);
            
            return template
                    .replace("[CANDIDATE_DATA]", candidateData.toString())
                    .replace("[JOB_DATA]", job.toString());
        } catch (Exception e) {
            log.error("Error reading prompt template, falling back to basic prompt", e);
            return "Atue como Kizuna Iporá. Crie um currículo em Markdown para a vaga: " + job.getTitle() + 
                   " usando os dados: " + candidateData.toString();
        }
    }

    private Mono<String> saveAndExport(String markdown, JobPosting job) {
        return Mono.fromCallable(() -> {
            String sanitizedTitle = job.getTitle().toString().replaceAll("[^a-zA-Z0-9]", "_");
            String fileName = "curriculo_" + sanitizedTitle + ".md";
            Path mdPath = Paths.get(CURRICULUMS_PATH, fileName);
            
            Files.createDirectories(mdPath.getParent());
            Files.writeString(mdPath, markdown);
            
            String pdfFileName = fileName.replace(".md", ".pdf");
            Path pdfPath = Paths.get(OUTPUT_PATH, pdfFileName);
            Files.createDirectories(pdfPath.getParent());
            
            pdfService.generatePdfFromMarkdown(markdown, pdfPath.toString());
            
            return pdfFileName;
        });
    }
}
