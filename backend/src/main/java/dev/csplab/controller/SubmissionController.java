package dev.csplab.controller;

import dev.csplab.dto.Requests;
import dev.csplab.repository.*;
import dev.csplab.service.SubmissionService;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api")
public class SubmissionController {
    private final SubmissionService service;
    private final SubmissionRepository repository;
    private final ProblemRepository problems;
    public SubmissionController(SubmissionService service, SubmissionRepository repository, ProblemRepository problems) { this.service=service; this.repository=repository; this.problems=problems; }
    @PostMapping("/submissions") @ResponseStatus(HttpStatus.ACCEPTED)
    public Map<String,Object> submit(@Valid @RequestBody Requests.Submit r) { return Map.of("id",service.submit(r,"JUDGE"),"status","QUEUED"); }
    @PostMapping("/runs") @ResponseStatus(HttpStatus.ACCEPTED)
    public Map<String,Object> run(@Valid @RequestBody Requests.Submit r) { return Map.of("id",service.submit(r,"SAMPLE"),"status","QUEUED"); }
    @GetMapping("/submissions/{id}") public Map<String,Object> detail(@PathVariable long id) { return repository.detail(id); }
    @GetMapping("/submissions") public Map<String,Object> list(@RequestParam(required=false) Long problemId,
        @RequestParam(required=false) Long examId, @RequestParam(required=false) String status,
        @RequestParam(defaultValue="1") @Min(1) @Max(100000) int page, @RequestParam(defaultValue="20") @Min(1) @Max(100) int size) { return repository.page(problemId,examId,status,page,size); }
    @GetMapping("/problems/{id}/draft") public Map<String,Object> draft(@PathVariable long id) { problems.get(id,false); return repository.draft(id,false); }
    @PutMapping("/problems/{id}/draft") public Map<String,Object> save(@PathVariable long id, @Valid @RequestBody Requests.Draft r) { return service.saveDraft(id,r); }
}
