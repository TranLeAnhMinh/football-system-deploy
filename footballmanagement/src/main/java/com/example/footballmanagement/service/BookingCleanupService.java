package com.example.footballmanagement.service;

import java.time.OffsetDateTime;

import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.example.footballmanagement.entity.enums.BookingStatus;
import com.example.footballmanagement.entity.enums.PaymentStatus;
import com.example.footballmanagement.repository.BookingRepository;
import com.example.footballmanagement.repository.PaymentRepository;

import lombok.RequiredArgsConstructor;
@Service
@RequiredArgsConstructor
public class BookingCleanupService {

    private final BookingRepository bookingRepo;
    private final BookingSlotService slotService;
    private final PaymentRepository paymentRepository;

    @Scheduled(fixedRate = 60000) // ✅ chạy mỗi 60 giây
    @Transactional
    public void cancelExpiredBookings() {
        // cutoff = hiện tại - 20 phút
        OffsetDateTime cutoff = OffsetDateTime.now().minusMinutes(20);

        // lấy danh sách booking PENDING mà createdAt < cutoff
        var expired = bookingRepo.findAllByStatusAndCreatedAtBefore(
                BookingStatus.PENDING,
                cutoff
        );

        if (!expired.isEmpty()) {
            expired.forEach(b -> {
                if (paymentRepository.existsByBooking_IdAndStatus(b.getId(), PaymentStatus.INITIATED)) {
                    return;
                }
                b.setStatus(BookingStatus.CANCELLED);
                slotService.deleteByBookingId(b.getId()); //    xoá slot đi
            });
            bookingRepo.saveAll(expired);
            System.out.println("Cancelled " + expired.size() + " expired bookings");
        }
    }

    @Scheduled(fixedRate = 60000)
    @Transactional
    public void cancelExpiredInitiatedPayments() {
        OffsetDateTime cutoff = OffsetDateTime.now().minusMinutes(20);
        var expiredPayments = paymentRepository.findByStatusAndCreatedAtBefore(
                PaymentStatus.INITIATED,
                cutoff
        );

        if (expiredPayments.isEmpty()) {
            return;
        }

        expiredPayments.forEach(payment -> {
            payment.setStatus(PaymentStatus.CANCELED);

            var booking = payment.getBooking();
            if (booking != null && booking.getStatus() == BookingStatus.PENDING) {
                booking.setStatus(BookingStatus.CANCELLED);
                slotService.deleteByBookingId(booking.getId());
            }
        });

        paymentRepository.saveAll(expiredPayments);
        System.out.println("Cancelled " + expiredPayments.size() + " expired initiated payments");
    }
}
