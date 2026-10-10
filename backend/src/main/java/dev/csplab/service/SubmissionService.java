package dev.csplab.service;

import dev.csplab.config.ApiException;
import dev.csplab.config.CurrentUser;
import dev.csplab.dto.Requests;
import dev.csplab.repository.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.nio.charset.StandardCharsets;
import java.util.*;

@Service
public class SubmissionService {
    private final SubmissionRepository submissions;
    private final ProblemRepository problems;
    private final ExamRepository exams;
    public SubmissionService(SubmissionRepository submissions, ProblemRepository problems, ExamRepository exams) {
        this.submissions=submissions; this.problems=problems; this.exams=exams;
    }
    @Transactional public long submit(Requests.Submit request, String mode) {
        validateSource(request.sourceCode());
        if(request.examId()==null && !"ADMIN".equals(CurrentUser.account().role())) throw ApiException.badRequest("请先开启模拟考试");
        // Serialize admission per account and enforce its queue limit atomically.
        exams.lockUser();
        if(request.examId()!=null) {
            var exam=exams.get(request.examId(),true);
            if(!"RUNNING".equals(exam.get("status")) || ((Number)exam.get("remainingSeconds")).longValue()<=0)
                throw ApiException.conflict("Exam has ended");
            if(!exams.contains(request.examId(),request.problemId())) throw ApiException.badRequest("Problem is not part of this exam");
        }
        var problem=problems.get(request.problemId(),true);
        if(mode.equals("JUDGE") && (!problem.get("evaluationType").equals("FULL") || !problem.get("constructionStatus").equals("VERIFIED")))
            throw ApiException.badRequest("This problem has no verified full evaluation dataset");
        if(mode.equals("SAMPLE") && problems.samples(request.problemId()).isEmpty()) throw ApiException.badRequest("No samples available");
        if(submissions.pending()>=20) throw ApiException.conflict("Queue limit reached; wait for earlier submissions");
        return submissions.create(request.problemId(),((Number)problem.get("version")).intValue(),request.sourceCode(),mode,request.examId());
    }
    @Transactional public Map<String,Object> saveDraft(long id, Requests.Draft request) {
        validateSource(request.sourceCode()); problems.get(id,true);
        var draft=submissions.draft(id,true);
        if(((Number)draft.get("revision")).longValue()!=request.revision()) throw ApiException.conflict("Draft was changed; load the latest revision before saving");
        submissions.saveDraft(id,request.sourceCode(),request.revision()); return submissions.draft(id,false);
    }
    private void validateSource(String source) {
        if(source.getBytes(StandardCharsets.UTF_8).length>65536) throw ApiException.badRequest("Source limit is 64 KiB UTF-8");
    }
}
