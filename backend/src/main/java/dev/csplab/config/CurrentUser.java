package dev.csplab.config;

import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.http.HttpStatus;
import java.io.Serializable;

public final class CurrentUser {
    private CurrentUser() {}
    public record Account(long id, String username, String displayName, String role, @com.fasterxml.jackson.annotation.JsonIgnore int authenticationVersion) implements Serializable {}
    public static Account account() {
        var auth=SecurityContextHolder.getContext().getAuthentication();
        if(auth==null || !(auth.getPrincipal() instanceof Account account))
            throw new ApiException(HttpStatus.UNAUTHORIZED,"请先登录");
        return account;
    }
    public static long id() { return account().id(); }
}
