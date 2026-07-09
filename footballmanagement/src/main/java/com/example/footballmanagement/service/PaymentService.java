package com.example.footballmanagement.service;

import java.util.Map;
import java.util.UUID;

import com.example.footballmanagement.entity.Payment;

import jakarta.servlet.http.HttpServletRequest;

public interface PaymentService {
    String createPaymentUrl(UUID bookingId, UUID userId, HttpServletRequest request) throws Exception;
    Payment handleVnPayReturn(Map<String, String> params) throws Exception;
    Map<String, String> handleVnPayIpn(Map<String, String> params);
}
