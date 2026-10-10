package dev.csplab;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class CspLabApplication {
    public static void main(String[] args) {
        SpringApplication.run(CspLabApplication.class, args);
    }
}
