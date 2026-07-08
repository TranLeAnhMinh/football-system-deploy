package com.example.footballmanagement.service;

import java.time.OffsetDateTime;

import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.example.footballmanagement.entity.enums.BookingStatus;
import com.example.footballmanagement.repository.BookingRepository;

import lombok.RequiredArgsConstructor;
@Service
@RequiredArgsConstructor
public class BookingCleanupService {

    private final BookingRepository bookingRepo;
    private final BookingSlotService slotService;

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
                b.setStatus(BookingStatus.CANCELLED);
                slotService.deleteByBookingId(b.getId()); //    xoá slot đi
            });
            bookingRepo.saveAll(expired);
            System.out.println("Cancelled " + expired.size() + " expired bookings");
        }
    }
}