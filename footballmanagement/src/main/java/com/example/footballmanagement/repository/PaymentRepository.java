package com.example.footballmanagement.repository;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import com.example.footballmanagement.entity.Payment;
import com.example.footballmanagement.entity.enums.BookingStatus;
import com.example.footballmanagement.entity.enums.PaymentStatus;


public interface PaymentRepository extends JpaRepository<Payment, UUID> {
    Optional<Payment> findByTxnRef(String txnRef);
    boolean existsByBooking_IdAndStatus(UUID bookingId, PaymentStatus status);
    List<Payment> findByBooking_IdInOrderByCreatedAtDesc(List<UUID> bookingIds);
    List<Payment> findByStatusAndCreatedAtBefore(PaymentStatus status, OffsetDateTime cutoff);

    @Query("""
        SELECT p.id
        FROM Payment p
        JOIN p.booking b
        WHERE (p.status = :initiatedStatus AND p.createdAt < :initiatedCutoff)
           OR (p.status = :paidStatus AND b.status NOT IN :paidBookingStatuses)
           OR (p.amount <> b.finalPrice)
           OR (p.responseCode = '00' AND p.transactionStatus = '00' AND p.status <> :paidStatus)
        ORDER BY p.createdAt DESC
    """)
    Page<UUID> findAnomalyPaymentIds(
            @Param("initiatedStatus") PaymentStatus initiatedStatus,
            @Param("initiatedCutoff") OffsetDateTime initiatedCutoff,
            @Param("paidStatus") PaymentStatus paidStatus,
            @Param("paidBookingStatuses") List<BookingStatus> paidBookingStatuses,
            Pageable pageable
    );

    @Query("""
        SELECT p
        FROM Payment p
        JOIN FETCH p.booking b
        JOIN FETCH b.user u
        JOIN FETCH b.branch br
        LEFT JOIN FETCH b.pitch pitch
        WHERE p.id IN :ids
    """)
    List<Payment> findAnomaliesWithDetailsByIds(@Param("ids") List<UUID> ids);
}
