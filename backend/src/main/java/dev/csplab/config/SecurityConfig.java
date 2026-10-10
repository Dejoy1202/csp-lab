package dev.csplab.config;

import jakarta.servlet.*;
import jakarta.servlet.http.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.*;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.security.web.context.HttpSessionSecurityContextRepository;
import org.springframework.security.web.csrf.HttpSessionCsrfTokenRepository;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.web.filter.OncePerRequestFilter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.List;

@Configuration
public class SecurityConfig {
    private final byte[] toolKey;
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;
    public SecurityConfig(@Value("${csp.api-key}") String key,org.springframework.jdbc.core.JdbcTemplate jdbc) {
        this.jdbc=jdbc;
        toolKey=key.getBytes(StandardCharsets.UTF_8);
    }
    @Bean PasswordEncoder passwordEncoder() { return new BCryptPasswordEncoder(12); }
    @Bean HttpSessionSecurityContextRepository contextRepository() { return new HttpSessionSecurityContextRepository(); }
    @Bean HttpSessionCsrfTokenRepository csrfRepository() { return new HttpSessionCsrfTokenRepository(); }
    private boolean toolRequest(HttpServletRequest request) {
        String key=request.getHeader("X-API-Key");
        return toolKey.length>=20 && key!=null && MessageDigest.isEqual(toolKey,key.getBytes(StandardCharsets.UTF_8));
    }
    @Bean SecurityFilterChain security(HttpSecurity http, HttpSessionSecurityContextRepository context,
                                     HttpSessionCsrfTokenRepository csrf) throws Exception {
        http.cors(cors -> {}).csrf(config -> config.csrfTokenRepository(csrf).ignoringRequestMatchers(this::toolRequest))
            .securityContext(config -> config.securityContextRepository(context))
            .authorizeHttpRequests(config -> config
                .requestMatchers("/actuator/health", "/api/auth/csrf", "/api/auth/login", "/api/auth/register").permitAll()
                .requestMatchers("/api/admin/**").hasRole("ADMIN")
                .requestMatchers("/api/**").authenticated().anyRequest().denyAll())
            .exceptionHandling(config -> config
                .authenticationEntryPoint((req,res,error) -> jsonError(res,401,"UNAUTHORIZED","请先登录"))
                .accessDeniedHandler((req,res,error) -> jsonError(res,403,"FORBIDDEN","无权访问或请求校验已过期，请刷新后重试")))
            .logout(config -> config.disable())
            .addFilterBefore(new OncePerRequestFilter() {
                @Override protected void doFilterInternal(HttpServletRequest req,HttpServletResponse res,FilterChain chain) throws ServletException,IOException {
                    // Retain a secret credential for offline pack-builder/testing tools.
                    // Browsers use HttpOnly sessions and never receive or send this key.
                    if(SecurityContextHolder.getContext().getAuthentication()==null && toolRequest(req)) {
                        var account=new CurrentUser.Account(1,"tool","题包管理工具","ADMIN",0);
                        SecurityContextHolder.getContext().setAuthentication(UsernamePasswordAuthenticationToken.authenticated(
                            account,null,List.of(new SimpleGrantedAuthority("ROLE_ADMIN"))));
                    }
                    var auth=SecurityContextHolder.getContext().getAuthentication();
                    if(!toolRequest(req) && auth!=null && auth.getPrincipal() instanceof CurrentUser.Account account) {
                        var versions=jdbc.queryForList("SELECT auth_version FROM users WHERE id=?",Integer.class,account.id());
                        if(versions.isEmpty() || versions.getFirst()!=account.authenticationVersion()) {
                            var session=req.getSession(false);if(session!=null) session.invalidate();
                            SecurityContextHolder.clearContext();
                        }
                    }
                    chain.doFilter(req,res);
                }
            },org.springframework.security.web.csrf.CsrfFilter.class);
        return http.build();
    }
    private static void jsonError(HttpServletResponse response,int status,String code,String message) throws IOException {
        response.setStatus(status); response.setContentType("application/json;charset=UTF-8");
        response.getWriter().write("{\"code\":\""+code+"\",\"message\":\""+message+"\"}");
    }
}
