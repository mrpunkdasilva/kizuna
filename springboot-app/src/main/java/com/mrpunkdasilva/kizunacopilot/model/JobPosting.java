package com.mrpunkdasilva.kizunacopilot.model;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Document(collection = "job_postings")
public class JobPosting {
    @Id
    private String id;
    private String title;
    private String company;
    private String location;
    private String description;
    private String sourceUrl; // To store the URL from which the job was scraped
}
