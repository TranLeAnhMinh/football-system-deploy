package com.example.footballmanagement.controller.api;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.example.footballmanagement.dto.response.PaymentAnomalyResponse;
import com.example.footballmanagement.service.AdminSystemPaymentService;

import lombok.RequiredArgsConstructor;

@RestController
@RequestMapping("/api/adminsystem/payments")
@RequiredArgsConstructor
public class AdminSystemPaymentController {

    private final AdminSystemPaymentService paymentService;

    @GetMapping("/anomalies")
    public ResponseEntity<Page<PaymentAnomalyResponse>> getAnomalies(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size
    ) {
        Pageable pageable = PageRequest.of(page, size, Sort.by("createdAt").descending());
        return ResponseEntity.ok(paymentService.getPaymentAnomalies(pageable));
    }
}
