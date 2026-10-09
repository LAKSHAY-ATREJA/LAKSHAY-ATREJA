package com.lakshay.ordermesh;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;
import org.junit.jupiter.api.Test;
import java.math.BigDecimal;
import java.util.Optional;

class OrderServiceTest {
    @Test void createsOrderAndOutboxEventAtomically() {
        var or = mock(OrderRepository.class); var ob = mock(OutboxRepository.class);
        when(or.findByIdempotencyKey("req-1")).thenReturn(Optional.empty());
        when(or.save(any())).thenAnswer(i -> i.getArgument(0));
        when(ob.save(any())).thenAnswer(i -> i.getArgument(0));
        var o = new OrderService(or, ob).create("req-1", "c1", new BigDecimal("19.99"));
        assertEquals("PENDING", o.status); verify(ob).save(any());
    }

    @Test void retryReturnsExistingOrderWithoutDuplicateEvent() {
        var or = mock(OrderRepository.class); var ob = mock(OutboxRepository.class);
        var existing = new Order("c1", new BigDecimal("19.99"), "req-1");
        when(or.findByIdempotencyKey("req-1")).thenReturn(Optional.of(existing));
        var actual = new OrderService(or, ob).create("req-1", "c1", new BigDecimal("19.99"));
        assertSame(existing, actual); verifyNoInteractions(ob); verify(or, never()).save(any());
    }
}
