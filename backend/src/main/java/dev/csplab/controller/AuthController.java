package dev.csplab.controller;

import dev.csplab.config.CurrentUser;
import dev.csplab.service.AccountService;
import jakarta.servlet.http.*;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import org.springframework.http.HttpStatus;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.context.HttpSessionSecurityContextRepository;
import org.springframework.security.web.csrf.*;
import org.springframework.web.bind.annotation.*;
import java.util.*;

@RestController
@RequestMapping("/api/auth")
public class AuthController {
    private final AccountService accounts;
    private final HttpSessionSecurityContextRepository contexts;
    private final HttpSessionCsrfTokenRepository csrf;
    public AuthController(AccountService accounts,HttpSessionSecurityContextRepository contexts,HttpSessionCsrfTokenRepository csrf) {
        this.accounts=accounts;this.contexts=contexts;this.csrf=csrf;
    }
    public record Credentials(@NotBlank @Size(max=64) String username,@NotNull @Size(min=8,max=72) String password) {}
    public record PasswordChange(@NotNull @Size(max=72) String previousPassword,@NotNull @Size(min=8,max=72) String newPassword) {}
    @GetMapping("/csrf") public Map<String,String> csrf(CsrfToken token) { return Map.of("token",token.getToken(),"headerName",token.getHeaderName()); }
    @GetMapping("/me") public CurrentUser.Account me() { return accounts.me(); }
    @PostMapping("/register") @ResponseStatus(HttpStatus.CREATED)
    public CurrentUser.Account register(@Valid @RequestBody Credentials input,HttpServletRequest request,HttpServletResponse response) {
        var user=accounts.register(input.username(),input.password());signIn(user,request,response);return user;
    }
    @PostMapping("/login") public CurrentUser.Account login(@Valid @RequestBody Credentials input,HttpServletRequest request,HttpServletResponse response) {
        var user=accounts.login(input.username(),input.password());signIn(user,request,response);return user;
    }
    private void signIn(CurrentUser.Account user,HttpServletRequest request,HttpServletResponse response) {
        request.getSession(true);request.changeSessionId(); // Prevent session fixation.
        var context=SecurityContextHolder.createEmptyContext();
        context.setAuthentication(UsernamePasswordAuthenticationToken.authenticated(user,null,List.of(new SimpleGrantedAuthority("ROLE_"+user.role()))));
        SecurityContextHolder.setContext(context);contexts.saveContext(context,request,response);
        csrf.saveToken(null,request,response);
    }
    @PostMapping("/logout") @ResponseStatus(HttpStatus.NO_CONTENT)
    public void logout(HttpServletRequest request,HttpServletResponse response) {
        var session=request.getSession(false);if(session!=null) session.invalidate();
        SecurityContextHolder.clearContext();
        var cookie=new Cookie("JSESSIONID","");cookie.setPath("/");cookie.setHttpOnly(true);cookie.setMaxAge(0);cookie.setAttribute("SameSite","Lax");response.addCookie(cookie);
    }
    @PostMapping("/password") @ResponseStatus(HttpStatus.NO_CONTENT)
    public void password(@Valid @RequestBody PasswordChange input,HttpServletRequest request,HttpServletResponse response) {
        accounts.changePassword(input.previousPassword(),input.newPassword());logout(request,response);
    }
}
