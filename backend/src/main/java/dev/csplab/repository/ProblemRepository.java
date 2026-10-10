package dev.csplab.repository;

import dev.csplab.config.ApiException;
import dev.csplab.config.CurrentUser;
import dev.csplab.dto.Requests;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.support.*;
import org.springframework.stereotype.Repository;
import java.sql.Statement;
import java.util.*;

@Repository
public class ProblemRepository {
    private final JdbcTemplate jdbc;
    public ProblemRepository(JdbcTemplate jdbc) { this.jdbc=jdbc; }
    public Map<String,Object> get(long id, boolean lock) {
        var rows = jdbc.query("SELECT * FROM problems WHERE id=?"+(lock ? " FOR UPDATE" : ""), Rows.MAPPER, id);
        if (rows.isEmpty()) throw ApiException.notFound("Problem not found");
        return rows.getFirst();
    }
    public Map<String,Object> page(Integer year, String batch, String difficulty, String tag, String status, int page, int size) {
        var where = new StringBuilder(" WHERE 1=1"); var args=new ArrayList<Object>(); args.add(CurrentUser.id());
        if (year!=null) { where.append(" AND p.source_year=?"); args.add(year); }
        if (batch!=null) { where.append(" AND p.source_batch=?"); args.add(batch); }
        if (difficulty!=null) { where.append(" AND p.difficulty=?"); args.add(difficulty); }
        if (tag!=null) { where.append(" AND JSON_CONTAINS(p.tags, JSON_QUOTE(?))"); args.add(tag); }
        String solved = "EXISTS(SELECT 1 FROM submissions s WHERE s.problem_id=p.id AND s.user_id=viewer.uid AND s.mode='JUDGE' AND s.status='AC' AND s.problem_version=p.version)";
        String attempted = "EXISTS(SELECT 1 FROM submissions s WHERE s.problem_id=p.id AND s.user_id=viewer.uid AND s.mode='JUDGE' AND s.problem_version=p.version)";
        if ("SOLVED".equals(status)) where.append(" AND ").append(solved);
        else if ("ATTEMPTED".equals(status)) where.append(" AND ").append(attempted).append(" AND NOT ").append(solved);
        else if ("UNSOLVED".equals(status)) where.append(" AND NOT ").append(attempted);
        long total=jdbc.queryForObject("SELECT COUNT(*) FROM problems p CROSS JOIN (SELECT ? AS uid) viewer"+where, Long.class, args.toArray());
        args.add(size); args.add((page-1)*size);
        var items=jdbc.query("SELECT p.id,p.code,p.title,p.source_year,p.source_batch,p.source_position,p.difficulty,p.tags,p.evaluation_type,p.construction_status,p.time_limit_ms,p.memory_limit_mb,p.source_url,p.version,CASE WHEN "+solved+" THEN 'SOLVED' WHEN "+attempted+" THEN 'ATTEMPTED' ELSE 'UNSOLVED' END AS completion_status FROM problems p CROSS JOIN (SELECT ? AS uid) viewer"+where+" ORDER BY p.id LIMIT ? OFFSET ?", Rows.MAPPER, args.toArray());
        return Map.of("items",items,"total",total,"page",page,"size",size);
    }
    public List<Map<String,Object>> samples(long id) {
        return jdbc.query("SELECT ordinal,input_data,expected_output,checker_type FROM problem_samples WHERE problem_id=? ORDER BY ordinal",Rows.MAPPER,id);
    }
    public List<Map<String,Object>> scoring(long id) {
        return jdbc.query("SELECT ordinal,score,subtask_key,checker_type FROM test_cases WHERE problem_id=? ORDER BY ordinal",Rows.MAPPER,id);
    }
    public List<Map<String,Object>> subtasks(long id) { return jdbc.query("SELECT subtask_key,label,score FROM problem_subtasks WHERE problem_id=? ORDER BY subtask_key",Rows.MAPPER,id); }
    public List<Map<String,Object>> assets(long id) { return jdbc.query("SELECT name,kind,sha256 FROM problem_assets WHERE problem_id=? ORDER BY name",Rows.MAPPER,id); }
    public Map<String,Object> asset(long id, String name) {
        var list=jdbc.query("SELECT name,kind,sha256,content FROM problem_assets WHERE problem_id=? AND name=?",Rows.MAPPER,id,name);
        if(list.isEmpty()) throw ApiException.notFound("Asset not found");return list.getFirst();
    }
    public Map<String,Object> version(long id,int version) {
        var values=jdbc.queryForList("SELECT public_snapshot FROM problem_versions WHERE problem_id=? AND version=?",String.class,id,version);
        if(values.isEmpty()) throw ApiException.notFound("Problem version not found");
        try { return new com.fasterxml.jackson.databind.ObjectMapper().readValue(values.getFirst(),new com.fasterxml.jackson.core.type.TypeReference<Map<String,Object>>(){}); }
        catch(com.fasterxml.jackson.core.JsonProcessingException e) { throw new IllegalStateException("Invalid version snapshot",e); }
    }
    public void snapshot(long id) {
        var data=get(id,false);data.put("samples",samples(id));data.put("scoring",scoring(id));data.put("subtasks",subtasks(id));data.put("assets",assets(id));
        jdbc.update("INSERT INTO problem_versions(problem_id,version,public_snapshot) VALUES(?,?,?)",id,data.get("version"),Rows.json(data));
    }
    public long insert(Requests.Problem p) {
        KeyHolder key=new GeneratedKeyHolder();
        jdbc.update(connection -> {
            var ps=connection.prepareStatement("INSERT INTO problems(code,title,source_year,source_batch,source_position,difficulty,tags,time_limit_ms,memory_limit_mb,source_url,statement,input_description,output_description,evaluation_type,license) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",Statement.RETURN_GENERATED_KEYS);
            Object[] values=values(p);
            for(int i=0;i<values.length;i++) ps.setObject(i+1,values[i]);
            return ps;
        },key);
        long id=Objects.requireNonNull(key.getKey()).longValue(); replaceCases(id,p); return id;
    }
    public void update(long id, Requests.Problem p) {
        var values=new ArrayList<>(Arrays.asList(values(p))); values.add(id);
        jdbc.update("UPDATE problems SET code=?,title=?,source_year=?,source_batch=?,source_position=?,difficulty=?,tags=?,time_limit_ms=?,memory_limit_mb=?,source_url=?,statement=?,input_description=?,output_description=?,evaluation_type=?,license=?,version=version+1 WHERE id=?",values.toArray());
        replaceCases(id,p);
    }
    public boolean inUse(long id) {
        return jdbc.queryForObject("SELECT (EXISTS(SELECT 1 FROM submissions WHERE problem_id=? AND status IN ('QUEUED','RUNNING')) OR EXISTS(SELECT 1 FROM mock_exam_problems ep JOIN mock_exams e ON e.id=ep.exam_id WHERE ep.problem_id=? AND e.status='RUNNING'))", Boolean.class,id,id);
    }
    private Object[] values(Requests.Problem p) {
        return new Object[]{p.code(),p.title(),p.sourceYear(),p.sourceBatch(),p.sourcePosition(),p.difficulty(),Rows.json(p.tags()),p.timeLimitMs(),p.memoryLimitMb(),p.sourceUrl(),p.statement(),p.inputDescription(),p.outputDescription(),p.evaluationType(),p.license()};
    }
    private void replaceCases(long id, Requests.Problem p) {
        jdbc.update("DELETE FROM problem_samples WHERE problem_id=?",id);
        jdbc.update("DELETE FROM test_cases WHERE problem_id=?",id);
        jdbc.update("DELETE FROM problem_subtasks WHERE problem_id=?",id);
        jdbc.update("DELETE FROM problem_assets WHERE problem_id=?",id);
        jdbc.update("UPDATE problems SET construction_status=?,constraints_description=?,scoring_notes=?,output_limit_kb=?,validation_report=? WHERE id=?",p.constructionStatus(),p.constraintsDescription(),p.scoringNotes(),p.outputLimitKb(),p.validationReport(),id);
        for(var s:p.subtasks()) jdbc.update("INSERT INTO problem_subtasks(problem_id,subtask_key,label,score) VALUES(?,?,?,?)",id,s.key(),s.label(),s.score());
        for(var a:p.assets()) {
            String hash;
            try { hash=HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(a.content().getBytes(java.nio.charset.StandardCharsets.UTF_8))); }
            catch(java.security.NoSuchAlgorithmException e) { throw new IllegalStateException(e); }
            jdbc.update("INSERT INTO problem_assets(problem_id,name,kind,sha256,content) VALUES(?,?,?,?,?)",id,a.name(),a.kind(),hash,a.content());
        }
        int ordinal=0;
        for (var s:p.samples()) jdbc.update("INSERT INTO problem_samples(problem_id,ordinal,input_data,expected_output,checker_type) VALUES(?,?,?,?,?)",id,++ordinal,s.input(),s.output(),s.checkerType());
        ordinal=0;
        for (var t:p.testCases()) jdbc.update("INSERT INTO test_cases(problem_id,ordinal,score,input_data,expected_output,subtask_key,checker_type) VALUES(?,?,?,?,?,?,?)",id,++ordinal,t.score(),t.input(),t.output(),t.subtaskKey(),t.checkerType());
    }
}
