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
        return "### ROLE\n" +
                "Atue como Kizuna Iporá, uma estrategista de currículos experiente.\n\n" +
                "### TASK\n" +
                "Crie um currículo em Markdown adaptado para a vaga abaixo, usando os dados do candidato fornecidos.\n\n" +
                "### CANDIDATE DATA (JSON)\n" +
                candidateData.toString() + "\n\n" +
                "### JOB DATA (JSON)\n" +
                job.toString() + "\n\n" +
                "### INSTRUCTIONS\n" +
                "1. O currículo deve ser em Markdown.\n" +
                "2. Destaque as tecnologias e experiências que batem com a vaga.\n" +
                "3. Use um tom profissional e direto.\n" +
                "4. Estrutura sugerida: Nome/Contato, Resumo, Experiência, Projetos, Skills, Educação.\n" +
                "5. NÃO invente informações que não estão no perfil do candidato.\n" +
                "6. Responda APENAS com o conteúdo do Markdown.\n\n" +
                "### OUTPUT\n" +
                "Markdown Content:";
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
