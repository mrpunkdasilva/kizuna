package com.mrpunkdasilva.kizunacopilot.service;

import lombok.Data;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.util.Map;

@Service
@Slf4j
public class OllamaService {

    private final WebClient webClient;

    @Value("${ollama.host:http://ollama:11434}")
    private String ollamaHost;

    @Value("${ollama.model:deepseek-r1:1.5b}")
    private String ollamaModel;

    public OllamaService(WebClient.Builder webClientBuilder) {
        this.webClient = webClientBuilder.build();
    }

    public Mono<String> generateContent(String prompt) {
        log.info("Generating content with Ollama model: {}", ollamaModel);
        
        Map<String, Object> requestBody = Map.of(
                "model", ollamaModel,
                "prompt", prompt,
                "stream", false,
                "options", Map.of("temperature", 0.3)
        );

        return webClient.post()
                .uri(ollamaHost + "/api/generate")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(requestBody)
                .retrieve()
                .bodyToMono(OllamaResponse.class)
                .timeout(Duration.ofMinutes(5))
                .map(response -> {
                    String text = response.getResponse();
                    // Remove think tags if present (DeepSeek specific)
                    if (text.contains("</think>")) {
                        text = text.split("</think>")[1].trim();
                    }
                    return text;
                })
                .doOnError(e -> log.error("Error calling Ollama: {}", e.getMessage()));
    }

    @Data
    private static class OllamaResponse {
        private String response;
    }
}
