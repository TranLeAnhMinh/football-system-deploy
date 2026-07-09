package com.example.footballmanagement.dto.response;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.UUID;

import com.example.footballmanagement.entity.enums.PaymentStatus;
import com.example.footballmanagement.entity.enums.PaymentType;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class PaymentInfoResponse {
    private UUID paymentId;
    private BigDecimal amount;
    private String method;
    private PaymentType type;
    private PaymentStatus status;
    private String txnRef;
    private String vnpTransactionNo;
    private String bankCode;
    private String responseCode;
    private String transactionStatus;
    private String payDate;
    private OffsetDateTime createdAt;
}
