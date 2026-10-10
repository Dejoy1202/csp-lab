package dev.csplab.service;

import dev.csplab.config.*;
import dev.csplab.config.CurrentUser.Account;
import dev.csplab.repository.AccountRepository;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.http.HttpStatus;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import java.nio.charset.StandardCharsets;

@Service
public class AccountService implements ApplicationRunner {
    private final AccountRepository repository;
    private final PasswordEncoder passwords;
    private final String ownerUsername,initialPassword,dummyHash;
    public AccountService(AccountRepository repository,PasswordEncoder passwords,
        @Value("${csp.admin-username:cspadmin}") String username,@Value("${csp.admin-initial-password:}") String password) {
        this.repository=repository;this.passwords=passwords;ownerUsername=username;initialPassword=password;
        dummyHash=passwords.encode("csp-dummy-account-do-not-use");
    }
    @Override public void run(ApplicationArguments args) {
        if(repository.ownerNeedsPassword()) {
            if(initialPassword.isBlank()) throw new IllegalStateException("Set ADMIN_INITIAL_PASSWORD before first startup");
            validatePassword(initialPassword);
            repository.initializeOwner(ownerUsername,passwords.encode(initialPassword));
        }
    }
    private String normalize(String username) {
        String value=username.trim().toLowerCase(java.util.Locale.ROOT);
        if(!value.matches("[a-z0-9_]{3,32}")) throw ApiException.badRequest("用户名须为3～32位字母、数字或下划线");
        return value;
    }
    private void validatePassword(String password) {
        if(password.length()<8 || password.getBytes(StandardCharsets.UTF_8).length>72)
            throw ApiException.badRequest("密码至少8位，UTF-8长度不超过72字节");
    }
    public Account register(String username,String password) {
        String name=normalize(username);validatePassword(password);
        try { return repository.create(name,passwords.encode(password)); }
        catch(DuplicateKeyException error) { throw ApiException.conflict("用户名已被使用"); }
    }
    public Account login(String username,String password) {
        String name=normalize(username);
        if(repository.recentFailures(name)>=10) throw new ApiException(HttpStatus.TOO_MANY_REQUESTS,"尝试次数过多，请15分钟后再试");
        var credential=repository.find(name);
        String hash=credential.map(AccountRepository.Credentials::passwordHash).orElse(null);
        boolean matches=passwords.matches(password,hash==null?dummyHash:hash);
        if(hash==null || !matches) {
            repository.failed(name);
            throw new ApiException(HttpStatus.UNAUTHORIZED,"用户名或密码错误");
        }
        repository.clearFailures(name);return credential.orElseThrow().account();
    }
    public Account me() { return repository.get(CurrentUser.id()); }
    public void changePassword(String previous,String next) {
        var user=me();login(user.username(),previous);validatePassword(next);
        repository.changePassword(user.id(),passwords.encode(next));
    }
}
