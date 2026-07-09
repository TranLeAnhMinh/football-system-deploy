package com.example.footballmanagement.repository;

import java.util.Optional;
import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;

import com.example.footballmanagement.entity.Payment;
import com.example.footballmanagement.entity.enums.PaymentStatus;


public interface PaymentRepository extends JpaRepository<Payment, UUID> {
    Optional<Payment> findByTxnRef(String txnRef);
    boolean existsByBooking_IdAndStatus(UUID bookingId, PaymentStatus status);
}
