package com.mrpunkdasilva.kizunacopilot.model;

import com.fasterxml.jackson.annotation.JsonProperty;
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
    
    private Object title;
    private Object company;
    private Object location;
    
    @JsonProperty("work_style")
    private Object workStyle;
    
    @JsonProperty("employment_type")
    private Object employmentType;
    
    private Object seniority;
    private Object salary;
    private Object description;
    private Object requirements;
    private Object benefits;
    
    @JsonProperty("posted_at")
    private Object postedAt;
    
    @JsonProperty("applications_count")
    private Object applicationsCount;
    
    private String sourceUrl;

    // AI Insights by Kizuna
    @JsonProperty("tech_stack")
    private Object techStack;
    
    @JsonProperty("soft_skills")
    private Object softSkills;
    
    private Object pros;
    private Object cons;
    
    @JsonProperty("ai_summary")
    private Object aiSummary;
    
    @JsonProperty("interview_tips")
    private Object interviewTips;
    
    @JsonProperty("ats_keywords")
    private Object atsKeywords;
    
    @JsonProperty("compatibility_score")
    private Object compatibilityScore;
    
    @JsonProperty("company_values")
    private Object companyValues;
}
