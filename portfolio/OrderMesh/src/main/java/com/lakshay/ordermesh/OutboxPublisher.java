package com.lakshay.ordermesh;
import org.springframework.kafka.core.KafkaTemplate; import org.springframework.scheduling.annotation.*; import org.springframework.stereotype.Component; import org.springframework.transaction.annotation.Transactional; import java.util.concurrent.TimeUnit;
@org.springframework.boot.autoconfigure.condition.ConditionalOnProperty(name="outbox.enabled", havingValue="true", matchIfMissing=true)
@Component @EnableScheduling public class OutboxPublisher { private final OutboxRepository repo; private final KafkaTemplate<String,String> kafka; public OutboxPublisher(OutboxRepository r,KafkaTemplate<String,String> k){repo=r;kafka=k;}
 @Scheduled(fixedDelayString="${outbox.poll-ms:1000}") @Transactional public void publish() throws Exception { for(var e:repo.findTop100ByPublishedFalseOrderByCreatedAtAsc()){ kafka.send("orders.events",e.aggregateId,e.payload).get(5,TimeUnit.SECONDS); e.published=true; } }
}
