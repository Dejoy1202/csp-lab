package dev.csplab.config;

import com.fasterxml.jackson.core.StreamReadConstraints;
import org.springframework.boot.autoconfigure.jackson.Jackson2ObjectMapperBuilderCustomizer;
import org.springframework.context.annotation.*;

@Configuration
public class JsonConfig {
    @Bean Jackson2ObjectMapperBuilderCustomizer largeTestInputs() {
        return builder -> builder.postConfigurer(mapper -> mapper.getFactory().setStreamReadConstraints(
            StreamReadConstraints.builder().maxStringLength(64*1024*1024).maxNestingDepth(32).build()));
    }
}
