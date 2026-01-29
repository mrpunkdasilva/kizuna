package com.mrpunkdasilva.kizunacopilot.repository;

import com.mrpunkdasilva.kizunacopilot.model.JobPosting;
import org.springframework.data.mongodb.repository.ReactiveMongoRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface JobPostingRepository extends ReactiveMongoRepository<JobPosting, String> {
}
