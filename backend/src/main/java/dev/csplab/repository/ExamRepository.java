package dev.csplab.repository;

import dev.csplab.config.ApiException;
import dev.csplab.config.CurrentUser;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.support.*;
import org.springframework.stereotype.Repository;
import java.sql.Statement;
import java.util.*;

@Repository
public class ExamRepository {
    private final JdbcTemplate jdbc;
    public ExamRepository(JdbcTemplate jdbc) { this.jdbc=jdbc; }
    public void lockUser() { jdbc.queryForObject("SELECT id FROM users WHERE id=? FOR UPDATE",Long.class,CurrentUser.id()); }
    public Map<String,Object> get(long id, boolean lock) {
        var rows=jdbc.query("SELECT *,NOW(6) AS server_now,CASE WHEN status='RUNNING' THEN GREATEST(0,CEIL(TIMESTAMPDIFF(MICROSECOND,NOW(6),ends_at)/1000000)) ELSE 0 END AS remaining_seconds FROM mock_exams WHERE id=? AND user_id=?"+(lock?" FOR UPDATE":""),Rows.MAPPER,id,CurrentUser.id());
        if(rows.isEmpty()) throw ApiException.notFound("Exam not found"); return rows.getFirst();
    }
    public boolean running() { return jdbc.queryForObject("SELECT EXISTS(SELECT 1 FROM mock_exams WHERE user_id=? AND status='RUNNING' AND ends_at>NOW(6))",Boolean.class,CurrentUser.id()); }
    public long create(String title) {
        KeyHolder key=new GeneratedKeyHolder();
        jdbc.update(c -> {
            var ps=c.prepareStatement("INSERT INTO mock_exams(user_id,title,ends_at) VALUES(?,?,DATE_ADD(NOW(6),INTERVAL 4 HOUR))",Statement.RETURN_GENERATED_KEYS);
            ps.setLong(1,CurrentUser.id()); ps.setString(2,title); return ps;
        },key);
        return Objects.requireNonNull(key.getKey()).longValue();
    }
    public void add(long exam, long problem, int ordinal, int version) {
        jdbc.update("INSERT INTO mock_exam_problems(exam_id,problem_id,ordinal,problem_version) VALUES(?,?,?,?)",exam,problem,ordinal,version);
    }
    public boolean contains(long exam, long problem) { return jdbc.queryForObject("SELECT EXISTS(SELECT 1 FROM mock_exam_problems WHERE exam_id=? AND problem_id=?)",Boolean.class,exam,problem); }
    public void finish(long id) { jdbc.update("UPDATE mock_exams SET status='FINISHED',finished_at=LEAST(NOW(6),ends_at) WHERE id=? AND status='RUNNING'",id); }
    public int expire() { return jdbc.update("UPDATE mock_exams SET status='FINISHED',finished_at=ends_at WHERE status='RUNNING' AND ends_at<=NOW(6)"); }
    public List<Map<String,Object>> scores(long id) {
        return jdbc.query("SELECT ep.ordinal,p.id AS problem_id,p.code,p.title,ep.problem_version,COALESCE(MAX(s.score),0) AS score,COALESCE(SUM(s.status IN ('QUEUED','RUNNING')),0) AS pending_submissions FROM mock_exam_problems ep JOIN problems p ON p.id=ep.problem_id LEFT JOIN submissions s ON s.exam_id=ep.exam_id AND s.problem_id=ep.problem_id AND s.mode='JUDGE' WHERE ep.exam_id=? GROUP BY ep.ordinal,p.id,p.code,p.title,ep.problem_version ORDER BY ep.ordinal",Rows.MAPPER,id);
    }
    public List<Map<String,Object>> list() {
        return jdbc.query("SELECT e.*,COALESCE((SELECT SUM(best) FROM (SELECT exam_id,problem_id,MAX(score) AS best FROM submissions WHERE mode='JUDGE' GROUP BY exam_id,problem_id) x WHERE x.exam_id=e.id),0) AS total_score FROM mock_exams e WHERE user_id=? ORDER BY id DESC LIMIT 100",Rows.MAPPER,CurrentUser.id());
    }
}
