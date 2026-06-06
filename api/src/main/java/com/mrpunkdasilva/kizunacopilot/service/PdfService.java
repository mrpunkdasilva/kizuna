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

        // 1. Convert Markdown to HTML
        MutableDataSet options = new MutableDataSet();
        Parser parser = Parser.builder(options).build();
        HtmlRenderer renderer = HtmlRenderer.builder(options).build();

        String htmlContent = renderer.render(parser.parse(markdownContent));

        // 2. Add professional CSS styling
        String styledHtml = "<html><head><style>" +
                "body { font-family: Arial, sans-serif; line-height: 1.5; color: #333; margin: 40px; font-size: 11pt; }" +
                "h1 { color: #000; text-align: center; border-bottom: 2px solid #000; padding-bottom: 10px; text-transform: uppercase; font-size: 22pt; margin-bottom: 5px; }" +
                "h2 { color: #004a99; border-bottom: 1px solid #ddd; margin-top: 20px; padding-bottom: 5px; text-transform: uppercase; font-size: 14pt; }" +
                "h3 { color: #333; margin-top: 12px; margin-bottom: 3px; font-size: 12pt; }" +
                "p { margin: 4px 0; }" +
                "ul { margin-top: 5px; padding-left: 20px; }" +
                "li { margin-bottom: 2px; }" +
                "strong { color: #000; font-weight: bold; }" +
                "a { color: #004a99; text-decoration: none; }" +
                "em { color: #555; font-style: italic; }" +
                ".summary { margin-top: 10px; text-align: center; font-size: 9pt; color: #555; }" +
                "</style></head><body>" + htmlContent + "</body></html>";

        // 3. Render HTML to PDF
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
