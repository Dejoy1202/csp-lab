package dev.csplab.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import java.util.List;

public final class Requests {
    private Requests() {}
    public record Sample(@NotNull @Size(max=262144) String input,
                         @NotNull @Size(max=262144) String output,
                         @Pattern(regexp="TOKENS|FLOAT_ABS_1E_3|FLOAT_ABS_1E_4|CSP_GROUP_COUNT|CSP_GROUP_PARTITION") String checkerType) {
        public Sample { if(checkerType==null) checkerType="TOKENS"; }
        public Sample(String input,String output) { this(input,output,"TOKENS"); }
    }
    public record TestCase(@NotNull @Size(max=67108864) String input,
                           @NotNull @Size(max=16777216) String output,
                           @Min(0) @Max(100) int score, @Pattern(regexp="[A-Za-z0-9_-]{1,32}") String subtaskKey,
                           @Pattern(regexp="TOKENS|FLOAT_ABS_1E_3|FLOAT_ABS_1E_4|CSP_GROUP_COUNT|CSP_GROUP_PARTITION") String checkerType) {
        public TestCase { if(checkerType==null) checkerType="TOKENS"; }
        public TestCase(String input,String output,int score,String subtaskKey) { this(input,output,score,subtaskKey,"TOKENS"); }
    }
    public record Subtask(@NotBlank @Pattern(regexp="[A-Za-z0-9_-]{1,32}") String key,
                          @NotBlank @Size(max=160) String label, @Min(1) @Max(100) int score) {}
    public record Asset(@NotBlank @Pattern(regexp="[A-Za-z0-9_.-]{1,128}") String name,
                        @NotNull @Pattern(regexp="GENERATOR|REFERENCE|VALIDATOR|REPORT") String kind,
                        @NotNull @Size(max=2097152) String content) {}
    public record Problem(@NotBlank @Pattern(regexp="[A-Za-z0-9_-]{1,64}") String code,
                          @NotBlank @Size(max=160) String title,
                          @Min(2013) @Max(2100) Integer sourceYear,
                          @NotBlank @Size(max=32) String sourceBatch,
                          @Min(1) @Max(5) Integer sourcePosition,
                          @NotNull @Pattern(regexp="EASY|MEDIUM|HARD") String difficulty,
                          @NotNull @Size(max=12) List<@NotBlank @Size(max=32) String> tags,
                          @Min(100) @Max(10000) int timeLimitMs,
                          @Min(32) @Max(1024) int memoryLimitMb,
                          @Size(max=1024) String sourceUrl,
                          @Size(max=65536) String statement,
                          @Size(max=8192) String inputDescription,
                          @Size(max=8192) String outputDescription,
                          @NotNull @Pattern(regexp="FULL|SAMPLE_ONLY|EXTERNAL_LINK") String evaluationType,
                          @NotBlank @Size(max=256) String license,
                          @NotNull @Size(max=10) List<@Valid Sample> samples,
                          @NotNull @Size(max=100) List<@Valid TestCase> testCases,
                          @NotNull @Pattern(regexp="BUILDING|VERIFIED") String constructionStatus,
                          @NotBlank @Size(max=8192) String constraintsDescription,
                          @NotBlank @Size(max=8192) String scoringNotes,
                          @Min(64) @Max(16384) int outputLimitKb,
                          @NotNull @Size(max=12) List<@Valid Subtask> subtasks,
                          @NotNull @Size(max=12) List<@Valid Asset> assets,
                          @Size(max=65536) String validationReport) {}
    public record ProblemBatch(@NotNull @Size(min=1,max=20) List<@Valid Problem> problems) {}
    public record Submit(@Positive long problemId, @NotBlank @Size(max=65536) String sourceCode,
                         @NotNull @Pattern(regexp="CPP17") String language, @Positive Long examId) {}
    public record Draft(@NotNull @Size(max=65536) String sourceCode, @PositiveOrZero long revision) {}
    public record Note(@NotNull @Size(max=10000) String content,
                       @NotNull @Size(max=12) List<@NotBlank @Size(max=32) String> customTags, boolean mastered) {}
    public record StartPractice(@Positive long problemId) {}
    public record StartExam(@Size(max=160) String title,
                            @Size(min=5, max=5) List<@Positive Long> problemIds,
                            @Pattern(regexp="[0-9]{6}") String batch) {}
}
