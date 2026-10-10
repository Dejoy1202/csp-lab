package dev.csplab.config;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.*;
@Configuration
public class WebConfig implements WebMvcConfigurer {
 private final String[] origins;
 public WebConfig(@Value("${csp.cors-origins}") String origins) { this.origins=origins.split(","); }
 @Override public void addCorsMappings(CorsRegistry registry) {
  registry.addMapping("/api/**").allowedOrigins(origins).allowedMethods("GET","POST","PUT","DELETE","OPTIONS")
   .allowedHeaders("Content-Type","X-CSRF-TOKEN","X-API-Key").allowCredentials(true).maxAge(3600);
 }
}
