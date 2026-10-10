package dev.csplab.repository;

import dev.csplab.config.CurrentUser.Account;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.support.*;
import org.springframework.stereotype.Repository;
import java.sql.Statement;
import java.util.*;

@Repository
public class AccountRepository {
    private final JdbcTemplate jdbc;
    public AccountRepository(JdbcTemplate jdbc) { this.jdbc=jdbc; }
    public record Credentials(Account account,String passwordHash) {}
    public Optional<Credentials> find(String username) {
        var rows=jdbc.query("SELECT id,username,display_name,role,auth_version,password_hash FROM users WHERE username=?",
            (rs,n)->new Credentials(new Account(rs.getLong("id"),rs.getString("username"),rs.getString("display_name"),rs.getString("role"),rs.getInt("auth_version")),rs.getString("password_hash")),username);
        return rows.stream().findFirst();
    }
    public Account get(long id) {
        return jdbc.queryForObject("SELECT id,username,display_name,role,auth_version FROM users WHERE id=?",
            (rs,n)->new Account(rs.getLong("id"),rs.getString("username"),rs.getString("display_name"),rs.getString("role"),rs.getInt("auth_version")),id);
    }
    public Account create(String username,String hash) {
        var key=new GeneratedKeyHolder();
        jdbc.update(c -> {var ps=c.prepareStatement("INSERT INTO users(username,display_name,password_hash) VALUES(?,?,?)",Statement.RETURN_GENERATED_KEYS);
            ps.setString(1,username);ps.setString(2,username);ps.setString(3,hash);return ps;},key);
        return get(Objects.requireNonNull(key.getKey()).longValue());
    }
    public void initializeOwner(String username,String hash) {
        jdbc.update("UPDATE users SET username=?,display_name=?,password_hash=? WHERE id=1 AND password_hash IS NULL",username,username,hash);
    }
    public boolean ownerNeedsPassword() { return jdbc.queryForObject("SELECT password_hash IS NULL FROM users WHERE id=1",Boolean.class); }
    public int recentFailures(String username) {
        return jdbc.query("SELECT IF(window_start>DATE_SUB(NOW(6),INTERVAL 15 MINUTE),attempts,0) FROM auth_failures WHERE username=?",
            (rs,n)->rs.getInt(1),username).stream().findFirst().orElse(0);
    }
    public void failed(String username) {
        jdbc.update("INSERT INTO auth_failures(username,attempts) VALUES(?,1) ON DUPLICATE KEY UPDATE attempts=IF(window_start>DATE_SUB(NOW(6),INTERVAL 15 MINUTE),attempts+1,1),window_start=IF(window_start>DATE_SUB(NOW(6),INTERVAL 15 MINUTE),window_start,NOW(6))",username);
    }
    public void clearFailures(String username) { jdbc.update("DELETE FROM auth_failures WHERE username=?",username); }
    public void changePassword(long id,String hash) { jdbc.update("UPDATE users SET password_hash=?,auth_version=auth_version+1 WHERE id=?",hash,id); }
}
