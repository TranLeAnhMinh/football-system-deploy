package com.example.footballmanagement.service;

import java.util.UUID;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

import com.example.footballmanagement.dto.response.PaymentAnomalyResponse;

public interface AdminSystemPaymentService {
    Page<PaymentAnomalyResponse> getPaymentAnomalies(Pageable pageable);
    PaymentAnomalyResponse reconcilePayment(UUID paymentId);
}
