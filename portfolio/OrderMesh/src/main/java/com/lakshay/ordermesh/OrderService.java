package com.lakshay.ordermesh;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.math.BigDecimal;

@Service
public class OrderService {
    private final OrderRepository orders;
    private final OutboxRepository outbox;

    public OrderService(OrderRepository orders, OutboxRepository outbox) {
        this.orders = orders;
        this.outbox = outbox;
    }
    public java.util.Optional<Order> find(java.util.UUID id) { return orders.findById(id); }

    @Transactional
    public Order create(String idempotencyKey, String customerId, BigDecimal amount) {
        if (idempotencyKey == null || idempotencyKey.isBlank()) throw new IllegalArgumentException("Idempotency-Key is required");
        if (amount == null || amount.signum() <= 0) throw new IllegalArgumentException("amount must be positive");
        if (customerId == null || customerId.isBlank()) throw new IllegalArgumentException("customerId is required");
        var existing = orders.findByIdempotencyKey(idempotencyKey);
        if (existing.isPresent()) {
            Order previous = existing.get();
            if (!previous.customerId.equals(customerId) || previous.amount.compareTo(amount) != 0)
                throw new IllegalArgumentException("idempotency key used for a different order");
            return previous;
        }
        return orders.findByIdempotencyKey(idempotencyKey).orElseGet(() -> {
            Order o = orders.save(new Order(customerId, amount, idempotencyKey));
            outbox.save(new OutboxEvent(o.id.toString(), "OrderCreated", "{\"orderId\":\"" + o.id + "\",\"amount\":\"" + amount + "\"}"));
            return o;
        });
    }
}
