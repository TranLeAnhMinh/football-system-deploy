package com.example.footballmanagement.repository;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Lock;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import com.example.footballmanagement.entity.Voucher;

import jakarta.persistence.LockModeType;

@Repository
public interface VoucherRepository extends JpaRepository<Voucher, UUID> {

    Optional<Voucher> findByCodeAndActiveTrue(String code);

    @Query("""
        SELECT v
        FROM Voucher v
        WHERE v.active = true
          AND (v.startAt IS NULL OR v.startAt <= :now)
          AND (v.endAt IS NULL OR v.endAt >= :now)
    """)
    List<Voucher> findAllValidVouchers(OffsetDateTime now);

    boolean existsByCode(String code);

    boolean existsByIdAndActiveTrue(UUID id);

    List<Voucher> findAllByOrderByCreatedAtDesc();

    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("SELECT v FROM Voucher v WHERE v.id = :id")
    Optional<Voucher> findByIdForUpdate(UUID id);
}