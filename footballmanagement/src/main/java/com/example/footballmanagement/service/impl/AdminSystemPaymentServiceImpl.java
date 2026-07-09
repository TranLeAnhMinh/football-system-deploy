package com.example.footballmanagement.service.impl;

import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.example.footballmanagement.dto.response.PaymentAnomalyResponse;
import com.example.footballmanagement.entity.Booking;
import com.example.footballmanagement.entity.Payment;
import com.example.footballmanagement.entity.enums.BookingStatus;
import com.example.footballmanagement.entity.enums.PaymentStatus;
import com.example.footballmanagement.repository.BookingRepository;
import com.example.footballmanagement.repository.PaymentRepository;
import com.example.footballmanagement.service.AdminSystemPaymentService;

import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class AdminSystemPaymentServiceImpl implements AdminSystemPaymentService {

    private static final int INITIATED_TIMEOUT_MINUTES = 20;
    private static final List<BookingStatus> PAID_BOOKING_STATUSES = List.of(
            BookingStatus.APPROVED,
            BookingStatus.CHECKED_IN,
            BookingStatus.NO_SHOW,
            BookingStatus.WAITING_REFUND,
            BookingStatus.REFUNDED
    );

    private final PaymentRepository paymentRepository;
    private final BookingRepository bookingRepository;

    @Override
    @Transactional(readOnly = true)
    public Page<PaymentAnomalyResponse> getPaymentAnomalies(Pageable pageable) {
        OffsetDateTime cutoff = OffsetDateTime.now().minusMinutes(INITIATED_TIMEOUT_MINUTES);
        Page<UUID> idPage = paymentRepository.findAnomalyPaymentIds(
                PaymentStatus.INITIATED,
                cutoff,
                PaymentStatus.PAID,
                PAID_BOOKING_STATUSES,
                pageable
        );

        if (idPage.isEmpty()) {
            return Page.empty(pageable);
        }

        Map<UUID, Integer> order = new java.util.HashMap<>();
        for (int i = 0; i < idPage.getContent().size(); i++) {
            order.put(idPage.getContent().get(i), i);
        }

        List<PaymentAnomalyResponse> content = paymentRepository
                .findAnomaliesWithDetailsByIds(idPage.getContent())
                .stream()
                .sorted(Comparator.comparingInt(payment -> order.getOrDefault(payment.getId(), Integer.MAX_VALUE)))
                .map(this::toResponse)
                .collect(Collectors.toList());

        return new PageImpl<>(content, pageable, idPage.getTotalElements());
    }

    @Override
    @Transactional
    public PaymentAnomalyResponse reconcilePayment(UUID paymentId) {
        Payment payment = paymentRepository.findById(paymentId)
                .orElseThrow(() -> new IllegalArgumentException("Payment not found"));
        Booking booking = payment.getBooking();
        if (booking == null) {
            throw new IllegalStateException("Payment does not have a booking");
        }
        if (payment.getAmount() == null
                || booking.getFinalPrice() == null
                || payment.getAmount().compareTo(booking.getFinalPrice()) != 0) {
            throw new IllegalStateException("Cannot reconcile payment with mismatched amount");
        }

        boolean vnpaySuccess = "00".equals(payment.getResponseCode())
                && "00".equals(payment.getTransactionStatus());
        if (payment.getStatus() != PaymentStatus.PAID && !vnpaySuccess) {
            throw new IllegalStateException("Payment is not confirmed as paid");
        }

        payment.setStatus(PaymentStatus.PAID);
        if (!PAID_BOOKING_STATUSES.contains(booking.getStatus())) {
            booking.setStatus(BookingStatus.APPROVED);
        }

        bookingRepository.save(booking);
        Payment saved = paymentRepository.save(payment);
        return toResponse(saved);
    }

    private PaymentAnomalyResponse toResponse(Payment payment) {
        Booking booking = payment.getBooking();
        return PaymentAnomalyResponse.builder()
                .paymentId(payment.getId())
                .bookingId(booking != null ? booking.getId() : null)
                .userFullName(booking != null && booking.getUser() != null ? booking.getUser().getFullName() : null)
                .userEmail(booking != null && booking.getUser() != null ? booking.getUser().getEmail() : null)
                .branchName(booking != null && booking.getBranch() != null ? booking.getBranch().getName() : null)
                .pitchName(booking != null && booking.getPitch() != null ? booking.getPitch().getName() : null)
                .paymentAmount(payment.getAmount())
                .bookingFinalPrice(booking != null ? booking.getFinalPrice() : null)
                .paymentStatus(payment.getStatus())
                .bookingStatus(booking != null ? booking.getStatus() : null)
                .txnRef(payment.getTxnRef())
                .vnpTransactionNo(payment.getVnpTransactionNo())
                .bankCode(payment.getBankCode())
                .responseCode(payment.getResponseCode())
                .transactionStatus(payment.getTransactionStatus())
                .payDate(payment.getPayDate())
                .paymentCreatedAt(payment.getCreatedAt())
                .reasons(reasons(payment, booking))
                .build();
    }

    private List<String> reasons(Payment payment, Booking booking) {
        List<String> reasons = new ArrayList<>();
        if (payment.getStatus() == PaymentStatus.INITIATED
                && payment.getCreatedAt().isBefore(OffsetDateTime.now().minusMinutes(INITIATED_TIMEOUT_MINUTES))) {
            reasons.add("Payment INITIATED quá 20 phút");
        }
        if (payment.getStatus() == PaymentStatus.PAID
                && booking != null
                && !PAID_BOOKING_STATUSES.contains(booking.getStatus())) {
            reasons.add("VNPay PAID nhưng booking chưa được xác nhận");
        }
        if (booking != null
                && payment.getAmount() != null
                && booking.getFinalPrice() != null
                && payment.getAmount().compareTo(booking.getFinalPrice()) != 0) {
            reasons.add("Số tiền payment lệch final price");
        }
        if (booking == null) {
            reasons.add("Payment không có booking tương ứng");
        }
        if ("00".equals(payment.getResponseCode())
                && "00".equals(payment.getTransactionStatus())
                && payment.getStatus() != PaymentStatus.PAID) {
            reasons.add("VNPay báo thành công nhưng payment không ở trạng thái PAID");
        }
        return reasons;
    }
}
