package com.lakshay.ordermesh;
import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.http.MediaType;

@SpringBootTest @AutoConfigureMockMvc @ActiveProfiles("demo")
class OrderApiTest {
    @Autowired MockMvc mvc;
    @Autowired OrderRepository orders;
    @Autowired OutboxRepository outbox;
    @Test void persistsOrderAndEventAndDeduplicatesRetry() throws Exception {
        long orderCount=orders.count(), eventCount=outbox.count();
        String body="{\"customerId\":\"demo\",\"amount\":19.99}";
        mvc.perform(post("/v1/orders").header("Idempotency-Key","api-test").contentType(MediaType.APPLICATION_JSON).content(body)).andExpect(status().isCreated());
        mvc.perform(post("/v1/orders").header("Idempotency-Key","api-test").contentType(MediaType.APPLICATION_JSON).content(body)).andExpect(status().isCreated());
        assertEquals(orderCount+1,orders.count()); assertEquals(eventCount+1,outbox.count());
        var order=orders.findByIdempotencyKey("api-test").orElseThrow();
        mvc.perform(get("/v1/orders/"+order.id)).andExpect(status().isOk()).andExpect(jsonPath("customerId").value("demo"));
        mvc.perform(post("/v1/orders").header("Idempotency-Key","api-test").contentType(MediaType.APPLICATION_JSON).content("{\"customerId\":\"other\",\"amount\":20}")).andExpect(status().isBadRequest());
    }
    @Test void rejectsInvalidAmountWithoutPersisting() throws Exception {
        long count=orders.count();
        mvc.perform(post("/v1/orders").header("Idempotency-Key","invalid").contentType(MediaType.APPLICATION_JSON).content("{\"customerId\":\"demo\",\"amount\":-5}")).andExpect(status().isBadRequest());
        assertEquals(count,orders.count());
        mvc.perform(get("/health")).andExpect(status().isOk());
    }
}
