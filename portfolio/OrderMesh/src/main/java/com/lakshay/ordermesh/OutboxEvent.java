package com.lakshay.ordermesh;
import jakarta.persistence.*; import java.time.Instant; import java.util.UUID;
@Entity @Table(name="outbox_events")
public class OutboxEvent { @Id public UUID id; public String aggregateId; public String type; @Column(length=4000) public String payload; public Instant createdAt; public boolean published;
 protected OutboxEvent(){} public OutboxEvent(String aggregateId,String type,String payload){id=UUID.randomUUID();this.aggregateId=aggregateId;this.type=type;this.payload=payload;createdAt=Instant.now();published=false;} }
