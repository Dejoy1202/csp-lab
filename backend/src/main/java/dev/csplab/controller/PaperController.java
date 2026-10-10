package dev.csplab.controller;
import dev.csplab.config.ApiException;
import dev.csplab.repository.Rows;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.*;
import java.util.*;
@RestController
@RequestMapping("/api/papers")
public class PaperController {
 private final JdbcTemplate jdbc;
 public PaperController(JdbcTemplate jdbc) { this.jdbc=jdbc; }
 @GetMapping public List<Map<String,Object>> list() {
  var papers=jdbc.query("SELECT batch AS source_batch,YEAR(CONCAT(batch,'01')) AS source_year,exam_number,exam_date,verified_metadata FROM csp_papers ORDER BY batch DESC",Rows.MAPPER);
  for(var paper:papers) {
   var p=problems((String)paper.get("sourceBatch"));
   long verified=p.stream().filter(this::verified).count();
   paper.put("problemCount",p.size());paper.put("verifiedCount",verified);paper.put("problems",p);
   paper.put("ready",ready(p));
  }
  return papers;
 }
 private List<Map<String,Object>> problems(String batch) {
  return jdbc.query("SELECT id,code,title,source_position,evaluation_type,construction_status FROM problems WHERE source_batch=? AND source_position BETWEEN 1 AND 5 ORDER BY source_position,id",Rows.MAPPER,batch);
 }
 private boolean verified(Map<String,Object> p) { return "FULL".equals(p.get("evaluationType")) && "VERIFIED".equals(p.get("constructionStatus")); }
 private boolean ready(List<Map<String,Object>> p) {
  return p.size()==5 && p.stream().allMatch(this::verified) && p.stream().map(q->q.get("sourcePosition")).distinct().count()==5;
 }
 @GetMapping("/{batch}") public Map<String,Object> paper(@PathVariable String batch) {
  var catalog=jdbc.query("SELECT batch,exam_number,exam_date FROM csp_papers WHERE batch=?",Rows.MAPPER,batch);
  if(catalog.isEmpty()) throw ApiException.notFound("考试批次不存在");
  var p=problems(batch); var result=catalog.getFirst();result.put("problems",p);result.put("ready",ready(p));
  result.put("durationSeconds",14400);result.put("maxScore",500);result.put("scoringType","SITE_SIMULATION");return result;
 }
}
