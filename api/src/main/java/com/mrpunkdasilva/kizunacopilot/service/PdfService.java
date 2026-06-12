package com.mrpunkdasilva.kizunacopilot.service;

import com.vladsch.flexmark.html.HtmlRenderer;
import com.vladsch.flexmark.parser.Parser;
import com.vladsch.flexmark.util.data.MutableDataSet;
import com.openhtmltopdf.pdfboxout.PdfRendererBuilder;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.io.FileOutputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;

@Service
@Slf4j
public class PdfService {

    public void generatePdfFromMarkdown(String markdownContent, String outputFilePath) throws Exception {
        log.info("Generating PDF at: {}", outputFilePath);

        // 1. Clean Markdown: Remove conversational filler and code blocks
        String cleanMarkdown = markdownContent;
        
        // Remove conversational preambles like "Sure, here is..."
        if (cleanMarkdown.contains("```markdown")) {
            cleanMarkdown = cleanMarkdown.split("```markdown")[1];
            if (cleanMarkdown.contains("```")) {
                cleanMarkdown = cleanMarkdown.split("```")[0];
            }
        } else if (cleanMarkdown.contains("```")) {
            // Fallback for just generic code blocks
            cleanMarkdown = cleanMarkdown.split("```")[1];
            if (cleanMarkdown.contains("```")) {
                cleanMarkdown = cleanMarkdown.split("```")[0];
            }
        }
        
        // Remove trailing conversational text if it's very long after the last section
        // (Simple heuristic: if there's a lot of text after the last header/list)
        cleanMarkdown = cleanMarkdown.trim();

        // 2. Convert Markdown to HTML
        MutableDataSet options = new MutableDataSet();
        Parser parser = Parser.builder(options).build();
        HtmlRenderer renderer = HtmlRenderer.builder(options).build();

        String htmlContent = renderer.render(parser.parse(cleanMarkdown));

        // 3. Add professional CSS styling
        String styledHtml = "<html><head><style>" +
                "@page { size: A4; margin: 2cm; }" +
                "body { font-family: 'Helvetica', 'Arial', sans-serif; line-height: 1.4; color: #333; font-size: 10.5pt; margin: 0; }" +
                "h1 { color: #000; text-align: center; border-bottom: 2px solid #2c3e50; padding-bottom: 5px; text-transform: uppercase; font-size: 18pt; margin-top: 0; margin-bottom: 10px; }" +
                "h2 { color: #2980b9; border-bottom: 1px solid #bdc3c7; margin-top: 15px; margin-bottom: 8px; padding-bottom: 3px; text-transform: uppercase; font-size: 13pt; font-weight: bold; }" +
                "h3 { color: #2c3e50; margin-top: 10px; margin-bottom: 2px; font-size: 11pt; font-weight: bold; }" +
                "p { margin: 3px 0; }" +
                "ul { margin: 5px 0; padding-left: 1.2em; }" +
                "li { margin-bottom: 2px; }" +
                "strong { color: #000; font-weight: bold; }" +
                "em { color: #7f8c8d; font-style: italic; }" +
                "hr { border: 0; border-top: 1px solid #eee; margin: 15px 0; }" +
                "</style></head><body>" + htmlContent + "</body></html>";

        // 4. Render HTML to PDF
        try (OutputStream os = new FileOutputStream(outputFilePath)) {
            PdfRendererBuilder builder = new PdfRendererBuilder();
            builder.useFastMode();
            builder.withHtmlContent(styledHtml, "");
            builder.toStream(os);
            builder.run();
        }

        log.info("PDF generated successfully!");
    }
}
