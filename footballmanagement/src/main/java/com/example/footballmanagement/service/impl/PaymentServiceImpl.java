package com.example.footballmanagement.service.impl;

import java.math.BigDecimal;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.security.InvalidKeyException;
import java.security.NoSuchAlgorithmException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.example.footballmanagement.config.VnPayConfig;
import com.example.footballmanagement.entity.Booking;
import com.example.footballmanagement.entity.Payment;
import com.example.footballmanagement.entity.enums.BookingStatus;
import com.example.footballmanagement.entity.enums.PaymentStatus;
import com.example.footballmanagement.repository.BookingRepository;
import com.example.footballmanagement.repository.PaymentRepository;
import com.example.footballmanagement.service.BookingSlotService;
import com.example.footballmanagement.service.PaymentService;

import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class PaymentServiceImpl implements PaymentService {

    private final VnPayConfig vnPayConfig;
    private final PaymentRepository paymentRepository;
    private final BookingRepository bookingRepository;
    private final BookingSlotService slotService;

    @Override
    @Transactional
    public String createPaymentUrl(UUID bookingId, UUID userId, HttpServletRequest request) throws Exception {
        Booking booking = bookingRepository.findById(bookingId)
                .orElseThrow(() -> new IllegalArgumentException("Booking not found"));

        if (!booking.getUser().getId().equals(userId)) {
            throw new SecurityException("You are not allowed to pay this booking");
        }
        if (booking.getStatus() != BookingStatus.PENDING) {
            throw new IllegalStateException("Only pending bookings can be paid");
        }

        BigDecimal finalPrice = booking.getFinalPrice();
        if (finalPrice == null || finalPrice.compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalStateException("Final price is not available for booking " + bookingId);
        }

        Payment payment = paymentRepository.save(Payment.builder()
                .booking(booking)
                .amount(finalPrice)
                .method("VNPAY")
                .txnRef(generateTxnRef())
                .status(PaymentStatus.INITIATED)
                .build());

        Map<String, String> params = new HashMap<>();
        params.put("vnp_Version", "2.1.0");
        params.put("vnp_Command", "pay");
        params.put("vnp_TmnCode", vnPayConfig.getTmnCode());
        params.put("vnp_Amount", String.valueOf(finalPrice.multiply(BigDecimal.valueOf(100)).longValue()));
        params.put("vnp_CurrCode", "VND");
        params.put("vnp_TxnRef", payment.getTxnRef());
        params.put("vnp_OrderInfo", "Thanh toan booking " + booking.getId());
        params.put("vnp_OrderType", "other");
        params.put("vnp_Locale", "vn");
        params.put("vnp_ReturnUrl", vnPayConfig.getReturnUrl());
        params.put("vnp_IpAddr", request.getRemoteAddr());
        params.put("vnp_CreateDate", new SimpleDateFormat("yyyyMMddHHmmss").format(new Date()));

        String hashData = buildHashData(params);
        StringBuilder query = new StringBuilder(hashData);

        String secureHash = hmacSHA512(vnPayConfig.getHashSecret(), hashData);
        query.append("&vnp_SecureHash=").append(secureHash);

        return vnPayConfig.getPayUrl() + "?" + query;
    }

    @Override
    @Transactional
    public Payment handleVnPayReturn(Map<String, String> vnpayParams) throws Exception {
        return processVnPayCallback(vnpayParams, false);
    }

    @Override
    @Transactional
    public Map<String, String> handleVnPayIpn(Map<String, String> vnpayParams) {
        try {
            processVnPayCallback(vnpayParams, true);
            return Map.of("RspCode", "00", "Message", "Confirm Success");
        } catch (AlreadyProcessedException e) {
            return Map.of("RspCode", "02", "Message", "Order already confirmed");
        } catch (PaymentNotFoundException e) {
            return Map.of("RspCode", "01", "Message", "Order not found");
        } catch (InvalidAmountException e) {
            return Map.of("RspCode", "04", "Message", "Invalid amount");
        } catch (InvalidChecksumException e) {
            return Map.of("RspCode", "97", "Message", "Invalid checksum");
        } catch (Exception e) {
            return Map.of("RspCode", "99", "Message", "Unknown error");
        }
    }

    private Payment processVnPayCallback(Map<String, String> vnpayParams, boolean reportAlreadyProcessed) {
        Map<String, String> params = new HashMap<>(vnpayParams);
        verifyChecksum(params);

        String txnRef = params.get("vnp_TxnRef");
        Payment payment = paymentRepository.findByTxnRef(txnRef)
                .orElseThrow(() -> new PaymentNotFoundException("Payment not found: " + txnRef));
        Booking booking = payment.getBooking();

        BigDecimal amount = new BigDecimal(params.get("vnp_Amount"))
                .divide(BigDecimal.valueOf(100));
        if (amount.compareTo(payment.getAmount()) != 0) {
            updateVnPayMetadata(payment, params);
            paymentRepository.save(payment);
            throw new InvalidAmountException("Invalid amount for payment " + txnRef);
        }

        updateVnPayMetadata(payment, params);

        if (payment.getStatus() != PaymentStatus.INITIATED) {
            paymentRepository.save(payment);
            if (reportAlreadyProcessed) {
                throw new AlreadyProcessedException("Payment already processed: " + txnRef);
            }
            return payment;
        }

        boolean success = "00".equals(params.get("vnp_ResponseCode"))
                && "00".equals(params.get("vnp_TransactionStatus"));

        payment.setStatus(success ? PaymentStatus.PAID : PaymentStatus.FAILED);

        if (success) {
            booking.setStatus(BookingStatus.APPROVED);
        } else if (!paymentRepository.existsByBooking_IdAndStatus(booking.getId(), PaymentStatus.PAID)) {
            booking.setStatus(BookingStatus.CANCELLED);
            slotService.deleteByBookingId(booking.getId());
        }

        bookingRepository.save(booking);
        return paymentRepository.save(payment);
    }

    private void verifyChecksum(Map<String, String> params) {
        String vnpSecureHash = params.get("vnp_SecureHash");

        params.remove("vnp_SecureHash");
        params.remove("vnp_SecureHashType");

        String calculatedHash = hmacSHA512(vnPayConfig.getHashSecret(), buildHashData(params));
        if (vnpSecureHash == null || !calculatedHash.equalsIgnoreCase(vnpSecureHash)) {
            throw new InvalidChecksumException("Invalid checksum from VNPAY");
        }
    }

    private void updateVnPayMetadata(Payment payment, Map<String, String> params) {
        payment.setVnpTransactionNo(params.get("vnp_TransactionNo"));
        payment.setBankCode(params.get("vnp_BankCode"));
        payment.setResponseCode(params.get("vnp_ResponseCode"));
        payment.setTransactionStatus(params.get("vnp_TransactionStatus"));
        payment.setPayDate(params.get("vnp_PayDate"));
        payment.setRawCallback(buildHashData(params));
    }

    private String generateTxnRef() {
        return "PAY-" + System.currentTimeMillis() + "-" + UUID.randomUUID().toString().substring(0, 8);
    }

    private String buildHashData(Map<String, String> params) {
        List<String> fieldNames = new ArrayList<>(params.keySet());
        Collections.sort(fieldNames);

        StringBuilder hashData = new StringBuilder();
        boolean first = true;

        for (String name : fieldNames) {
            String value = params.get(name);

            if (value != null && !value.isEmpty()) {
                if (!first) {
                    hashData.append('&');
                }
                hashData.append(name)
                        .append('=')
                        .append(URLEncoder.encode(value, StandardCharsets.US_ASCII));
                first = false;
            }
        }

        return hashData.toString();
    }

    private String hmacSHA512(String key, String data) {
        try {
            Mac hmac512 = Mac.getInstance("HmacSHA512");
            SecretKeySpec secretKeySpec =
                    new SecretKeySpec(key.getBytes(StandardCharsets.UTF_8), "HmacSHA512");

            hmac512.init(secretKeySpec);

            byte[] bytes = hmac512.doFinal(data.getBytes(StandardCharsets.UTF_8));
            StringBuilder hash = new StringBuilder();

            for (byte b : bytes) {
                hash.append(String.format("%02x", b));
            }

            return hash.toString();
        } catch (NoSuchAlgorithmException | InvalidKeyException e) {
            throw new RuntimeException("Error while generating HMAC SHA512 hash", e);
        }
    }

    private static class InvalidChecksumException extends RuntimeException {
        private InvalidChecksumException(String message) {
            super(message);
        }
    }

    private static class PaymentNotFoundException extends RuntimeException {
        private PaymentNotFoundException(String message) {
            super(message);
        }
    }

    private static class InvalidAmountException extends RuntimeException {
        private InvalidAmountException(String message) {
            super(message);
        }
    }

    private static class AlreadyProcessedException extends RuntimeException {
        private AlreadyProcessedException(String message) {
            super(message);
        }
    }
}
