package dev.csplab.repository;

import dev.csplab.config.ApiException;
import dev.csplab.config.CurrentUser;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.support.*;
import org.springframework.stereotype.Repository;
import java.sql.Statement;
import java.util.*;

@Repository
public class SubmissionRepository {
    private final JdbcTemplate jdbc;
    public SubmissionRepository(JdbcTemplate jdbc) { this.jdbc=jdbc; }
    public long create(long problemId, int version, String source, String mode, Long examId) {
        KeyHolder key=new GeneratedKeyHolder();
        jdbc.update(connection -> {
            var ps=connection.prepareStatement("INSERT INTO submissions(user_id,problem_id,problem_version,source_code,mode,exam_id,max_score) VALUES(?,?,?,?,?,?,?)",Statement.RETURN_GENERATED_KEYS);
            ps.setLong(1,CurrentUser.id()); ps.setLong(2,problemId); ps.setInt(3,version); ps.setString(4,source); ps.setString(5,mode); ps.setObject(6,examId); ps.setInt(7,mode.equals("JUDGE")?100:0);
            return ps;
        },key);
        return Objects.requireNonNull(key.getKey()).longValue();
    }
    public int pending() { return jdbc.queryForObject("SELECT COUNT(*) FROM submissions WHERE user_id=? AND status IN ('QUEUED','RUNNING')",Integer.class,CurrentUser.id()); }
    public Map<String,Object> detail(long id) {
        var rows=jdbc.query("SELECT s.*,p.code AS problem_code,p.title AS problem_title,p.evaluation_type FROM submissions s JOIN problems p ON p.id=s.problem_id WHERE s.id=? AND s.user_id=?",Rows.MAPPER,id,CurrentUser.id());
        if(rows.isEmpty()) throw ApiException.notFound("Submission not found");
        var row=rows.getFirst(); row.remove("workerId"); row.remove("leaseUntil");
        row.put("results",jdbc.query("SELECT ordinal,status,score,max_score,time_ms,memory_kb,stdout,stderr,subtask_key,exit_code,message FROM submission_results WHERE submission_id=? ORDER BY ordinal",Rows.MAPPER,id));
        row.put("subtasks",jdbc.query("SELECT subtask_key,status,score,max_score FROM submission_subtasks WHERE submission_id=? ORDER BY subtask_key",Rows.MAPPER,id));
        return row;
    }
    public Map<String,Object> page(Long problemId, Long examId, String status, int page, int size) {
        var where=new StringBuilder(" WHERE s.user_id=?"); var args=new ArrayList<Object>(); args.add(CurrentUser.id());
        if(problemId!=null) { where.append(" AND s.problem_id=?"); args.add(problemId); }
        if(examId!=null) { where.append(" AND s.exam_id=?"); args.add(examId); }
        if(status!=null) { where.append(" AND s.status=?"); args.add(status); }
        long total=jdbc.queryForObject("SELECT COUNT(*) FROM submissions s"+where,Long.class,args.toArray());
        args.add(size); args.add((page-1)*size);
        var items=jdbc.query("SELECT s.id,s.problem_id,p.code AS problem_code,p.title AS problem_title,s.problem_version,s.exam_id,s.mode,s.status,s.score,s.max_score,s.created_at,s.finished_at FROM submissions s JOIN problems p ON p.id=s.problem_id"+where+" ORDER BY s.id DESC LIMIT ? OFFSET ?",Rows.MAPPER,args.toArray());
        return Map.of("items",items,"total",total,"page",page,"size",size);
    }
    public Map<String,Object> draft(long id, boolean lock) {
        var rows=jdbc.query("SELECT source_code,revision,updated_at FROM code_drafts WHERE user_id=? AND problem_id=?"+(lock?" FOR UPDATE":""),Rows.MAPPER,CurrentUser.id(),id);
        return rows.isEmpty()?new LinkedHashMap<>(Map.of("sourceCode","","revision",0L)):rows.getFirst();
    }
    public void saveDraft(long id, String source, long revision) {
        if(revision==0) jdbc.update("INSERT INTO code_drafts(user_id,problem_id,source_code,revision) VALUES(?,?,?,1)",CurrentUser.id(),id,source);
        else jdbc.update("UPDATE code_drafts SET source_code=?,revision=revision+1 WHERE user_id=? AND problem_id=?",source,CurrentUser.id(),id);
    }
}
