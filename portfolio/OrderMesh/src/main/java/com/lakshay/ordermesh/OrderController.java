package com.lakshay.ordermesh;

import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import java.math.BigDecimal;

@RestController
@RequestMapping("/v1/orders")
public class OrderController {
    private final OrderService service;
    public OrderController(OrderService service) { this.service = service; }
    @GetMapping("/{id}")
    public ResponseEntity<Order> find(@PathVariable java.util.UUID id) {
        return service.find(id).map(ResponseEntity::ok).orElseGet(() -> ResponseEntity.notFound().build());
    }
    public record CreateOrder(String customerId, BigDecimal amount) {}

    @PostMapping
    public ResponseEntity<Order> create(@RequestHeader("Idempotency-Key") String key, @RequestBody CreateOrder body) {
        return ResponseEntity.status(HttpStatus.CREATED).body(service.create(key, body.customerId(), body.amount()));
    }
}
