package dev.csplab.controller;

import dev.csplab.dto.Requests;
import dev.csplab.repository.ExamRepository;
import dev.csplab.service.ExamService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import java.util.*;

@RestController
@RequestMapping("/api/exams")
public class ExamController {
    private final ExamService service;
    private final ExamRepository repository;
    public ExamController(ExamService service, ExamRepository repository) { this.service=service; this.repository=repository; }
    @PostMapping @ResponseStatus(HttpStatus.CREATED) public Map<String,Object> start(@Valid @RequestBody Requests.StartExam r) { return service.detail(service.start(r)); }
    @GetMapping public List<Map<String,Object>> list() { service.expire(); return repository.list(); }
    @GetMapping("/{id}") public Map<String,Object> detail(@PathVariable long id) { return service.detail(id); }
    @PostMapping("/{id}/finish") public Map<String,Object> finish(@PathVariable long id) { service.finish(id); return service.detail(id); }
}
