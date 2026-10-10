package dev.csplab.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import dev.csplab.config.ApiException;
import dev.csplab.dto.Requests;
import dev.csplab.repository.ProblemRepository;
import dev.csplab.service.ProblemService;
import jakarta.validation.*;
import jakarta.validation.constraints.*;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import java.io.IOException;
import java.io.InputStream;
import java.io.FilterInputStream;
import java.util.zip.GZIPInputStream;
import java.util.*;

@RestController
@RequestMapping("/api")
public class ProblemController {
    private final ProblemRepository repository;
    private final ProblemService service;
    private final ObjectMapper json;
    private final Validator validator;
    public ProblemController(ProblemRepository repository, ProblemService service, ObjectMapper json, Validator validator) {
        this.repository=repository; this.service=service; this.json=json; this.validator=validator;
    }
    @GetMapping("/problems") public Map<String,Object> list(@RequestParam(required=false) Integer year,
        @RequestParam(required=false) String batch, @RequestParam(required=false) String difficulty,
        @RequestParam(required=false) String tag, @RequestParam(required=false) String status,
        @RequestParam(defaultValue="1") @Min(1) @Max(100000) int page, @RequestParam(defaultValue="20") @Min(1) @Max(100) int size) {
        if(status!=null && !Set.of("SOLVED","ATTEMPTED","UNSOLVED").contains(status)) throw ApiException.badRequest("Invalid completion status");
        return repository.page(year,batch,difficulty,tag,status,page,size);
    }
    @GetMapping("/problems/{id}") public Map<String,Object> detail(@PathVariable long id) { return service.detail(id); }
    @GetMapping("/problems/{id}/versions/{version}") public Map<String,Object> version(@PathVariable long id,@PathVariable int version) { return repository.version(id,version); }
    @GetMapping("/admin/problems/{id}/assets/{name}") public Map<String,Object> asset(@PathVariable long id,@PathVariable String name) { return repository.asset(id,name); }
    @PostMapping("/admin/problems") @ResponseStatus(HttpStatus.CREATED)
    public Map<String,Object> create(@Valid @RequestBody Requests.Problem p) { return Map.of("id",service.create(p)); }
    @PutMapping("/admin/problems/{id}") public Map<String,Object> update(@PathVariable long id, @Valid @RequestBody Requests.Problem p) {
        service.update(id,p); return Map.of("id",id);
    }
    @PostMapping(value="/admin/problems/import",consumes="multipart/form-data") @ResponseStatus(HttpStatus.CREATED)
    public Map<String,Object> importJson(@RequestPart("file") MultipartFile file) throws IOException {
        Requests.Problem p;
        try { p=json.readValue(file.getInputStream(),Requests.Problem.class); }
        catch(IOException e) { throw ApiException.badRequest("Upload a valid UTF-8 problem JSON object"); }
        if(p==null) throw ApiException.badRequest("Problem cannot be null");
        var errors=validator.validate(p);
        if(!errors.isEmpty()) throw ApiException.badRequest(errors.iterator().next().getPropertyPath()+": invalid value");
        return Map.of("id",service.create(p));
    }
    @PostMapping("/admin/problems/batch") @ResponseStatus(HttpStatus.CREATED)
    public Map<String,Object> batch(@Valid @RequestBody Requests.ProblemBatch batch) { return Map.of("ids",service.createBatch(batch)); }
    @PostMapping(value="/admin/problems/import-pack",consumes="multipart/form-data") @ResponseStatus(HttpStatus.CREATED)
    public Map<String,Object> importPack(@RequestPart("file") MultipartFile file) throws IOException {
        Requests.ProblemBatch batch;
        try(InputStream stream=new LimitedStream(new GZIPInputStream(file.getInputStream()))) {
            batch=json.readValue(stream,Requests.ProblemBatch.class);
        } catch(IOException e) { throw ApiException.badRequest("Expected .json.gz pack with at most 128 MiB uncompressed JSON"); }
        if(batch==null) throw ApiException.badRequest("Pack cannot be null");
        var errors=validator.validate(batch);
        if(!errors.isEmpty()) throw ApiException.badRequest(errors.iterator().next().getPropertyPath()+": invalid value");
        return Map.of("ids",service.createBatch(batch));
    }
    private static class LimitedStream extends FilterInputStream {
        private long count;
        LimitedStream(InputStream stream) { super(stream); }
        @Override public int read() throws IOException { int b=in.read(); if(b>=0) check(1); return b; }
        @Override public int read(byte[] b,int off,int len) throws IOException { int n=in.read(b,off,len); if(n>0) check(n); return n; }
        private void check(int n) throws IOException { count+=n; if(count>128L*1024*1024) throw new IOException("Pack too large"); }
    }
}
