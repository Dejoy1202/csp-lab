package dev.csplab.repository;

import org.junit.jupiter.api.Test;
import java.sql.*;
import java.time.LocalDateTime;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class RowsTest {
    @Test void mysqlLocalDateTimesHaveExplicitShanghaiOffsetAndSnapshotSerializes() throws Exception {
        var rs=mock(ResultSet.class);var meta=mock(ResultSetMetaData.class);
        when(rs.getMetaData()).thenReturn(meta);when(meta.getColumnCount()).thenReturn(2);
        when(meta.getColumnLabel(1)).thenReturn("created_at");when(meta.getColumnLabel(2)).thenReturn("tags");
        when(rs.getObject(1)).thenReturn(LocalDateTime.of(2026,10,9,9,0));when(rs.getObject(2)).thenReturn("[\"高斯消元\"]");
        var row=Rows.MAPPER.mapRow(rs,0);
        assertEquals("2026-10-09T09:00+08:00",row.get("createdAt"));assertTrue(Rows.json(row).contains("高斯消元"));
    }
    @Test void sqlDateTrendIsADateString() throws Exception {
        var rs=mock(ResultSet.class);var meta=mock(ResultSetMetaData.class);
        when(rs.getMetaData()).thenReturn(meta);when(meta.getColumnCount()).thenReturn(1);when(meta.getColumnLabel(1)).thenReturn("day");
        when(rs.getObject(1)).thenReturn(Date.valueOf("2026-10-09"));
        assertEquals("2026-10-09",Rows.MAPPER.mapRow(rs,0).get("day"));
    }
}
