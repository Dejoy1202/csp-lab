package dev.csplab.service;

import dev.csplab.config.ApiException;
import dev.csplab.config.CurrentUser;
import org.springframework.jdbc.core.JdbcTemplate;
import dev.csplab.dto.Requests;
import dev.csplab.repository.*;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.util.*;

@Service
public class ExamService {
    private final ExamRepository exams;
    private final ProblemRepository problems;
    private final JdbcTemplate jdbc;
    public ExamService(ExamRepository exams, ProblemRepository problems,JdbcTemplate jdbc) { this.exams=exams; this.problems=problems; this.jdbc=jdbc; }
    @Transactional public long start(Requests.StartExam request) {
        exams.lockUser(); exams.expire();
        if(exams.running()) throw ApiException.conflict("Finish the running exam first");
        List<Long> ids=request.problemIds(); String title=request.title();
        if(request.batch()!=null) {
            var catalog=jdbc.queryForList("SELECT exam_number FROM csp_papers WHERE batch=?",Integer.class,request.batch());
            if(catalog.isEmpty()) throw ApiException.notFound("考试批次不存在");
            ids=jdbc.queryForList("SELECT id FROM problems WHERE source_batch=? AND source_position BETWEEN 1 AND 5 ORDER BY source_position",Long.class,request.batch());
            title=request.batch().substring(0,4)+" 年 "+Integer.parseInt(request.batch().substring(4))+" 月 CSP 模拟考试";
        } else if(!"ADMIN".equals(CurrentUser.account().role())) throw ApiException.badRequest("请选择 CSP 考试批次");
        if(ids==null || title==null || title.isBlank() || ids.size()!=5) throw ApiException.badRequest("试卷尚未完成建设");
        if(new HashSet<>(ids).size()!=5) throw ApiException.badRequest("Choose five distinct problems");
        var loaded=new HashMap<Long,Map<String,Object>>();
        for(long id:ids.stream().sorted().toList()) {
            var p=problems.get(id,true);
            if(!"FULL".equals(p.get("evaluationType")) || !"VERIFIED".equals(p.get("constructionStatus"))) throw ApiException.badRequest("All five problems need verified full datasets");
            loaded.put(id,p);
        }
        if(request.batch()!=null && loaded.values().stream().map(p->p.get("sourcePosition")).distinct().count()!=5)
            throw ApiException.badRequest("试卷必须包含真实的第1至第5题");
        long id=exams.create(title); int ordinal=0;
        for(long problemId:ids) exams.add(id,problemId,++ordinal,((Number)loaded.get(problemId).get("version")).intValue());
        return id;
    }
    public Map<String,Object> detail(long id) {
        var exam=exams.get(id,false);
        if("RUNNING".equals(exam.get("status")) && ((Number)exam.get("remainingSeconds")).longValue()==0) {
            exams.expire(); exam=exams.get(id,false);
        }
        var scores=exams.scores(id); exam.put("problems",scores);
        exam.put("totalScore",scores.stream().mapToLong(s->((Number)s.get("score")).longValue()).sum());
        exam.put("maxScore",500); exam.put("scoringType","SITE_SIMULATION");
        exam.put("pendingSubmissions",scores.stream().mapToLong(s->((Number)s.get("pendingSubmissions")).longValue()).sum());
        return exam;
    }
    @Transactional public void finish(long id) { exams.get(id,true); exams.finish(id); }
    @Scheduled(fixedDelay=5000) public void expire() { exams.expire(); }
}
