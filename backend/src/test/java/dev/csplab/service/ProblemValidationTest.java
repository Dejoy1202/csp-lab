package dev.csplab.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import dev.csplab.config.ApiException;
import dev.csplab.dto.Requests;
import org.junit.jupiter.api.Test;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class ProblemValidationTest {
    @Test void acceptsAdditionalRegressionChecksWithBoundedPackSize() {
        var point=new Requests.TestCase("1\n","1\n",0,"s1");
        var groups=List.of(new Requests.Subtask("s1","regression",100));
        try(var factory=jakarta.validation.Validation.buildDefaultValidatorFactory()) {
            for(int count:List.of(41,44,100,101)) {
                var p=problem("FULL","VERIFIED",Collections.nCopies(count,point),groups);
                assertEquals(count>100,!factory.getValidator().validate(p).isEmpty(),"checks="+count);
                if(count<=100)assertDoesNotThrow(()->ProblemService.validate(p));
            }
        }
    }
    private Requests.Problem problem(String type, String state, List<Requests.TestCase> cases, List<Requests.Subtask> groups) {
        return new Requests.Problem("TEST","题目",2024,"202403",1,"EASY",List.of("模拟"),1000,128,
            "https://example.com/problem","Authorized independently authored statement","input","output",type,"CSP Lab original",
            List.of(new Requests.Sample("1","1")),cases,state,"constraints","simulation",64,groups,List.of(),"{\"verified\":true}");
    }
    @Test void rejectsIncompleteHundredPointClaim() {
        assertThrows(ApiException.class,()->ProblemService.validate(problem("FULL","VERIFIED",List.of(new Requests.TestCase("1","1",20,null)),List.of())));
    }
    @Test void acceptsMixedIndependentAndBundledScoring() {
        assertDoesNotThrow(()->ProblemService.validate(problem("FULL","VERIFIED",List.of(new Requests.TestCase("1","1",20,null),new Requests.TestCase("2","2",0,"s1")),List.of(new Requests.Subtask("s1","group",80)))));
    }
    @Test void rejectsEmptyGroupAndDoubleCounting() {
        assertThrows(ApiException.class,()->ProblemService.validate(problem("FULL","VERIFIED",List.of(new Requests.TestCase("1","1",100,null)),List.of(new Requests.Subtask("s1","group",10)))));
        assertThrows(ApiException.class,()->ProblemService.validate(problem("FULL","VERIFIED",List.of(new Requests.TestCase("1","1",50,"s1")),List.of(new Requests.Subtask("s1","group",50)))));
    }
    @Test void distinguishesBuildingAndSampleOnly() {
        assertDoesNotThrow(()->ProblemService.validate(problem("FULL","BUILDING",List.of(),List.of())));
        assertDoesNotThrow(()->ProblemService.validate(problem("SAMPLE_ONLY","VERIFIED",List.of(),List.of())));
        assertThrows(ApiException.class,()->ProblemService.validate(problem("SAMPLE_ONLY","VERIFIED",List.of(new Requests.TestCase("1","1",100,null)),List.of())));
    }
    @Test void rejectsJavascriptSourceLinks() {
        var p=problem("FULL","BUILDING",List.of(),List.of());
        var unsafe=new Requests.Problem(p.code(),p.title(),p.sourceYear(),p.sourceBatch(),p.sourcePosition(),p.difficulty(),p.tags(),p.timeLimitMs(),p.memoryLimitMb(),"javascript:alert(1)",p.statement(),p.inputDescription(),p.outputDescription(),p.evaluationType(),p.license(),p.samples(),p.testCases(),p.constructionStatus(),p.constraintsDescription(),p.scoringNotes(),p.outputLimitKb(),p.subtasks(),p.assets(),p.validationReport());
        assertThrows(ApiException.class,()->ProblemService.validate(unsafe));
    }
    @Test void legacyPacksDefaultToTokenComparison() throws Exception {
        var mapper=new ObjectMapper();
        var sample=mapper.readValue("{\"input\":\"1\",\"output\":\"1\"}",Requests.Sample.class);
        var point=mapper.readValue("{\"input\":\"1\",\"output\":\"1\",\"score\":100}",Requests.TestCase.class);
        assertEquals("TOKENS",sample.checkerType());assertEquals("TOKENS",point.checkerType());
        var validator=jakarta.validation.Validation.buildDefaultValidatorFactory().getValidator();
        assertFalse(validator.validate(new Requests.TestCase("1","1",100,null,"EXECUTE_CODE")).isEmpty());
    }
    @Test void floatingCheckerIsWhitelistedWithoutExecutableCode() {
        try(var factory=jakarta.validation.Validation.buildDefaultValidatorFactory()) {
            var validator=factory.getValidator();
            for(String checker:List.of("FLOAT_ABS_1E_3","FLOAT_ABS_1E_4")) {
                assertTrue(validator.validate(new Requests.Sample("1","1",checker)).isEmpty());
                assertTrue(validator.validate(new Requests.TestCase("1","1",100,null,checker)).isEmpty());
            }
            assertTrue(validator.validate(new Requests.TestCase("1","1",100,null,"FLOAT_ABS_1E_3")).isEmpty());
            assertFalse(validator.validate(new Requests.TestCase("1","1",100,null,"CUSTOM_EXEC")).isEmpty());
        }
    }
    @Test void importedRecordsPreserveUnicode() throws Exception {
        var mapper=new ObjectMapper(); var p=problem("FULL","BUILDING",List.of(),List.of());
        assertEquals("题目",mapper.readValue(mapper.writeValueAsBytes(p),Requests.Problem.class).title());
    }
    @Test void permitsOneGiBButKeepsMemoryBounds() {
        var mapper=new ObjectMapper();
        var fields=mapper.convertValue(problem("FULL","BUILDING",List.of(),List.of()),
            new com.fasterxml.jackson.core.type.TypeReference<Map<String,Object>>() {});
        try(var factory=jakarta.validation.Validation.buildDefaultValidatorFactory()) {
            for(int memory:List.of(31,32,1024,1025)) {
                fields.put("memoryLimitMb",memory);
                var p=mapper.convertValue(fields,Requests.Problem.class);
                var errors=factory.getValidator().validate(p);
                assertEquals(memory==31 || memory==1025,!errors.isEmpty(),"memory="+memory);
            }
        }
    }
    @Test void permitsLargeCertificatesWithoutIncreasingSourceLimits() {
        var mapper=new ObjectMapper();
        var fields=mapper.convertValue(problem("FULL","BUILDING",List.of(),List.of()),
            new com.fasterxml.jackson.core.type.TypeReference<Map<String,Object>>() {});
        fields.put("assets",List.of(new Requests.Asset("certificates.json","REPORT","x".repeat(1027612))));
        var report=mapper.convertValue(fields,Requests.Problem.class);
        try(var factory=jakarta.validation.Validation.buildDefaultValidatorFactory()) {
            assertTrue(factory.getValidator().validate(report).isEmpty());
        }
        assertDoesNotThrow(()->ProblemService.validate(report));
        fields.put("assets",List.of(new Requests.Asset("generator.py","GENERATOR","x".repeat(262145))));
        assertThrows(ApiException.class,()->ProblemService.validate(mapper.convertValue(fields,Requests.Problem.class)));
    }
}
