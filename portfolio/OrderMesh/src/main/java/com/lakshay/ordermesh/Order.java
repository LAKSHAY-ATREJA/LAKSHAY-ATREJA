package com.lakshay.ordermesh;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "orders", uniqueConstraints = @UniqueConstraint(name = "uq_order_idempotency", columnNames = "idempotency_key"))
public class Order {
    @Id public UUID id;
    @Column(nullable = false) public String customerId;
    @Column(nullable = false) public BigDecimal amount;
    @Column(nullable = false) public String status;
    @Column(name = "idempotency_key", nullable = false) public String idempotencyKey;
    @Column(nullable = false) public Instant createdAt;

    protected Order() {}

    public Order(String customerId, BigDecimal amount, String idempotencyKey) {
        this.id = UUID.randomUUID();
        this.customerId = customerId;
        this.amount = amount;
        this.status = "PENDING";
        this.idempotencyKey = idempotencyKey;
        this.createdAt = Instant.now();
    }
}
