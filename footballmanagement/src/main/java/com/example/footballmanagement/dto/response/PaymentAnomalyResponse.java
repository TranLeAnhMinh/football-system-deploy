package com.example.footballmanagement.dto.response;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;

import com.example.footballmanagement.entity.enums.BookingStatus;
import com.example.footballmanagement.entity.enums.PaymentStatus;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class PaymentAnomalyResponse {
    private UUID paymentId;
    private UUID bookingId;
    private String userFullName;
    private String userEmail;
    private String branchName;
    private String pitchName;
    private BigDecimal paymentAmount;
    private BigDecimal bookingFinalPrice;
    private PaymentStatus paymentStatus;
    private BookingStatus bookingStatus;
    private String txnRef;
    private String vnpTransactionNo;
    private String bankCode;
    private String responseCode;
    private String transactionStatus;
    private String payDate;
    private OffsetDateTime paymentCreatedAt;
    private List<String> reasons;
}
