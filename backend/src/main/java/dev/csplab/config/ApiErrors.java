package dev.csplab.config;

import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.http.*;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.multipart.MaxUploadSizeExceededException;
import org.springframework.web.method.annotation.HandlerMethodValidationException;
import java.util.Map;

@RestControllerAdvice
public class ApiErrors {
    @ExceptionHandler(ApiException.class)
    ResponseEntity<?> api(ApiException e) { return response(e.status(), e.getMessage()); }
    @ExceptionHandler(MethodArgumentNotValidException.class)
    ResponseEntity<?> validation(MethodArgumentNotValidException e) {
        return response(HttpStatus.BAD_REQUEST, e.getBindingResult().getFieldErrors().stream()
            .map(x -> x.getField()+": "+x.getDefaultMessage()).findFirst().orElse("Invalid request"));
    }
    @ExceptionHandler({HttpMessageNotReadableException.class, HandlerMethodValidationException.class})
    ResponseEntity<?> malformed(Exception e) { return response(HttpStatus.BAD_REQUEST, "Invalid JSON or request parameters"); }
    @ExceptionHandler(DataIntegrityViolationException.class)
    ResponseEntity<?> duplicate(DataIntegrityViolationException e) { return response(HttpStatus.CONFLICT, "Duplicate code or inconsistent data"); }
    @ExceptionHandler(MaxUploadSizeExceededException.class)
    ResponseEntity<?> tooLarge(Exception e) { return response(HttpStatus.PAYLOAD_TOO_LARGE, "Upload limit is 32 MiB"); }
    @ExceptionHandler(org.springframework.web.servlet.resource.NoResourceFoundException.class)
    ResponseEntity<?> removed(Exception e) { return response(HttpStatus.NOT_FOUND,"接口不存在"); }
    @ExceptionHandler(Exception.class)
    ResponseEntity<?> internal(Exception e) {
        org.slf4j.LoggerFactory.getLogger(ApiErrors.class).error("Request failed",e);
        return response(HttpStatus.INTERNAL_SERVER_ERROR,"服务器处理失败，请稍后重试");
    }
    private ResponseEntity<?> response(HttpStatus status, String message) {
        return ResponseEntity.status(status).body(Map.of("code", status.name(), "message", message));
    }
}
