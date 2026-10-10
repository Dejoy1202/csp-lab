package dev.csplab.repository;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.jdbc.core.RowMapper;
import java.sql.Timestamp;
import java.time.ZoneOffset;
import java.util.*;

public final class Rows {
    private static final ObjectMapper JSON = new ObjectMapper();
    private Rows() {}
    public static final RowMapper<Map<String, Object>> MAPPER = (rs, rowNum) -> {
        var result = new LinkedHashMap<String, Object>();
        var meta = rs.getMetaData();
        for (int i=1; i<=meta.getColumnCount(); i++) {
            String key = camel(meta.getColumnLabel(i));
            Object value = rs.getObject(i);
            if (value instanceof Timestamp ts) value = ts.toLocalDateTime().atOffset(ZoneOffset.ofHours(8)).toString();
            else if(value instanceof java.time.LocalDateTime dt) value=dt.atOffset(ZoneOffset.ofHours(8)).toString();
            else if(value instanceof java.sql.Date date) value=date.toLocalDate().toString();
            else if(value instanceof java.time.LocalDate date) value=date.toString();
            if (value != null && (key.equals("tags") || key.equals("customTags"))) {
                try { value = JSON.readValue(value.toString(), List.class); }
                catch(JsonProcessingException e) { throw new java.sql.SQLException("Invalid stored JSON",e); }
            }
            result.put(key, value);
        }
        return result;
    };
    public static String json(Object value) {
        try { return JSON.writeValueAsString(value); }
        catch (JsonProcessingException e) { throw new IllegalArgumentException("Cannot serialize value", e); }
    }
    private static String camel(String input) {
        var result = new StringBuilder(); boolean upper = false;
        for (char c : input.toCharArray()) {
            if (c == '_') upper = true;
            else { result.append(upper ? Character.toUpperCase(c) : c); upper = false; }
        }
        return result.toString();
    }
}
