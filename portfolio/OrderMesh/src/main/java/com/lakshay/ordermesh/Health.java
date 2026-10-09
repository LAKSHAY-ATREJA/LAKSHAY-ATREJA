package com.lakshay.ordermesh;
import java.util.Map;
import org.springframework.web.bind.annotation.*;
@RestController
public class Health {
    @GetMapping("/health") public Map<String,String> health() { return Map.of("status", "ok"); }
}
