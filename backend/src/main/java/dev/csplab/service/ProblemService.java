package dev.csplab.service;

import dev.csplab.config.ApiException;
import dev.csplab.dto.Requests;
import dev.csplab.repository.ProblemRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.net.URI;
import java.util.*;

@Service
public class ProblemService {
    private final ProblemRepository repository;
    public ProblemService(ProblemRepository repository) { this.repository=repository; }
    public Map<String,Object> detail(long id) {
        var p=repository.get(id,false); p.put("samples",repository.samples(id)); p.put("scoring",repository.scoring(id));
        p.put("subtasks",repository.subtasks(id)); p.put("assets",repository.assets(id));
        return p;
    }
    @Transactional public long create(Requests.Problem p) { validate(p); long id=repository.insert(p); repository.snapshot(id); return id; }
    @Transactional public List<Long> createBatch(Requests.ProblemBatch batch) {
        for(var p:batch.problems()) validate(p);
        return batch.problems().stream().map(p -> {long id=repository.insert(p);repository.snapshot(id);return id;}).toList();
    }
    @Transactional public void update(long id, Requests.Problem p) {
        validate(p); repository.get(id,true);
        if(repository.inUse(id)) throw ApiException.conflict("Problem has queued submissions or a running exam; finish them before editing");
        repository.update(id,p);
        repository.snapshot(id);
    }
    public static void validate(Requests.Problem p) {
        for(var asset:p.assets()) {
            if(!"REPORT".equals(asset.kind()) && asset.content().length()>262144)
                throw ApiException.badRequest("Source assets must not exceed 262144 characters");
        }
        if(p.sourceUrl()!=null && !p.sourceUrl().isBlank()) {
            try {
                URI uri=URI.create(p.sourceUrl());
                if(!Set.of("http","https").contains(uri.getScheme()) || uri.getHost()==null) throw new IllegalArgumentException();
            } catch (IllegalArgumentException e) { throw ApiException.badRequest("sourceUrl must be an HTTP(S) link"); }
        }
        switch(p.evaluationType()) {
            case "FULL" -> {
                if(p.constructionStatus().equals("BUILDING")) break;
                if(p.testCases().isEmpty() || p.testCases().stream().mapToInt(Requests.TestCase::score).sum()+p.subtasks().stream().mapToInt(Requests.Subtask::score).sum()!=100)
                    throw ApiException.badRequest("FULL requires test cases totaling exactly 100 points");
                if(p.statement()==null || p.statement().isBlank()) throw ApiException.badRequest("FULL requires an authorized statement");
            }
            case "SAMPLE_ONLY" -> {
                if(p.samples().isEmpty() || !p.testCases().isEmpty()) throw ApiException.badRequest("SAMPLE_ONLY requires samples and no hidden tests");
            }
            case "EXTERNAL_LINK" -> {
                if(p.sourceUrl()==null || p.sourceUrl().isBlank() || !p.samples().isEmpty() || !p.testCases().isEmpty())
                    throw ApiException.badRequest("EXTERNAL_LINK requires a source URL and no local evaluation data");
            }
            default -> throw ApiException.badRequest("Unsupported evaluationType");
        }
        var keys=new HashSet<String>();
        for(var group:p.subtasks()) {
            if(!keys.add(group.key())) throw ApiException.badRequest("Duplicate subtask key");
            if(p.testCases().stream().noneMatch(c -> group.key().equals(c.subtaskKey()))) throw ApiException.badRequest("Subtask has no test cases");
        }
        for(var c:p.testCases()) {
            if(c.subtaskKey()!=null && (!keys.contains(c.subtaskKey()) || c.score()!=0)) throw ApiException.badRequest("Grouped cases must reference a subtask and use score=0");
            if(c.subtaskKey()==null && c.score()==0) throw ApiException.badRequest("Independent cases need positive scores");
        }
        if("VERIFIED".equals(p.constructionStatus()) && "FULL".equals(p.evaluationType()) && (p.validationReport()==null || p.validationReport().isBlank()))
            throw ApiException.badRequest("VERIFIED requires a validation report");
        if(p.validationReport()!=null) {
            try { new com.fasterxml.jackson.databind.ObjectMapper().readTree(p.validationReport()); }
            catch(com.fasterxml.jackson.core.JsonProcessingException e) { throw ApiException.badRequest("validationReport must be valid JSON text"); }
        }
    }
}
