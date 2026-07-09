package com.example.footballmanagement.service.impl;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;

import com.example.footballmanagement.dto.request.MaintenanceWindowRequest;
import com.example.footballmanagement.dto.response.BookingOverlapResponse;
import com.example.footballmanagement.dto.response.MaintenanceWindowResponse;
import com.example.footballmanagement.entity.Booking;
import com.example.footballmanagement.entity.MaintenanceWindow;
import com.example.footballmanagement.entity.Pitch;
import com.example.footballmanagement.entity.User;
import com.example.footballmanagement.entity.enums.BookingStatus;
import com.example.footballmanagement.entity.enums.UserRole;
import com.example.footballmanagement.entity.enums.UserStatus;
import com.example.footballmanagement.exception.ApiException;
import com.example.footballmanagement.exception.ErrorCode;
import com.example.footballmanagement.repository.BookingRepository;
import com.example.footballmanagement.repository.BookingSlotRepository;
import com.example.footballmanagement.repository.MaintenanceWindowRepository;
import com.example.footballmanagement.repository.PitchRepository;
import com.example.footballmanagement.repository.UserRepository;
import com.example.footballmanagement.service.EmailTemplateService;
import com.example.footballmanagement.service.MaintenanceWindowService;
import com.example.footballmanagement.utils.ConverterUtil;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class MaintenanceWindowServiceImpl implements MaintenanceWindowService {

    private final MaintenanceWindowRepository maintenanceRepo;
    private final BookingSlotRepository bookingSlotRepo;
    private final BookingRepository bookingRepo;
    private final PitchRepository pitchRepo;
    private final UserRepository userRepo;
    private final EmailTemplateService emailTemplateService;

    @Override
    public boolean existsOverlap(UUID pitchId, OffsetDateTime startAt, OffsetDateTime endAt) {
        return maintenanceRepo.existsOverlap(pitchId, startAt, endAt);
    }

    @Override
    public List<MaintenanceWindowResponse> getMaintenanceWindows(
            UUID pitchId,
            OffsetDateTime from,
            OffsetDateTime to
    ) {
        if (from != null && to != null) {
            return maintenanceRepo.findByPitch_IdAndEndAtAfterAndStartAtBefore(pitchId, from, to)
                    .stream()
                    .map(ConverterUtil::toMaintenanceWindowResponse)
                    .collect(Collectors.toList());
        }

        return maintenanceRepo.findByPitch_Id(pitchId)
                .stream()
                .map(ConverterUtil::toMaintenanceWindowResponse)
                .collect(Collectors.toList());
    }

    @Override
    public boolean checkConflict(UUID pitchId, OffsetDateTime startAt, OffsetDateTime endAt) {
        boolean conflictBooking = bookingSlotRepo.existsOverlap(pitchId, startAt, endAt);
        boolean conflictMaint = maintenanceRepo.existsOverlap(pitchId, startAt, endAt);
        return conflictBooking || conflictMaint;
    }

    @Override
    @Transactional
    public MaintenanceWindowResponse createMaintenanceWindow(UUID adminId, MaintenanceWindowRequest req) {
        log.info("[MAIN THREAD] Processing maintenance on thread: {}", Thread.currentThread().getName());

        User currentUser = userRepo.findById(adminId)
                .orElseThrow(() -> new ApiException(ErrorCode.USER_NOT_FOUND));

        validateMaintenanceTime(req);

        if (currentUser.getRole() != UserRole.ADMIN_BRANCH) {
            throw new ApiException(ErrorCode.PERMISSION_DENIED);
        }

        if (currentUser.getStatus() != UserStatus.ACTIVE) {
            throw new ApiException(ErrorCode.USER_INACTIVE);
        }

        //  Lock pitch trong suốt transaction để tránh race condition
Pitch pitch = pitchRepo.findByIdForUpdate(req.getPitchId())
        .orElseThrow(() -> new ApiException(ErrorCode.PITCH_NOT_FOUND));

        if (pitch.getBranch() == null ||
                pitch.getBranch().getAdmin() == null ||
                !pitch.getBranch().getAdmin().getId().equals(currentUser.getId())) {
            throw new ApiException(ErrorCode.PERMISSION_DENIED);
        }

        boolean conflictMaint = maintenanceRepo.existsOverlap(
                req.getPitchId(),
                req.getStartAt(),
                req.getEndAt()
        );

        if (conflictMaint) {
            throw new ApiException(ErrorCode.MAINTENANCE_CONFLICT);
        }

        var overlappedSlots = bookingSlotRepo.findOccupiedByPitch_IdAndRange(
        req.getPitchId(),
        req.getStartAt(),
        req.getEndAt()
);

boolean hasPending = overlappedSlots.stream()
        .anyMatch(slot -> slot.getBooking().getStatus() == BookingStatus.PENDING);

if (hasPending) {
    throw new ApiException(ErrorCode.PENDING_BOOKING_CONFLICT);
}

List<Booking> affectedBookings = overlappedSlots.stream()
        .map(slot -> slot.getBooking())
        .filter(booking -> booking.getStatus() == BookingStatus.APPROVED)
        .distinct()
        .toList();

if (!affectedBookings.isEmpty()) {
    affectedBookings.forEach(booking -> booking.setStatus(BookingStatus.WAITING_REFUND));
    bookingRepo.saveAll(affectedBookings);
}

        MaintenanceWindow window = MaintenanceWindow.builder()
                .pitch(pitch)
                .startAt(req.getStartAt())
                .endAt(req.getEndAt())
                .reason(req.getReason())
                .build();

        maintenanceRepo.save(window);

        MaintenanceWindowResponse response = ConverterUtil.toMaintenanceWindowResponse(window);

        if (!affectedBookings.isEmpty()) {
            List<Booking> finalAffectedBookings = affectedBookings;

            TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
                @Override
                public void afterCommit() {
                    log.info("Bắt đầu gửi email bảo trì async cho {} booking", finalAffectedBookings.size());

                    finalAffectedBookings.forEach(booking -> {
                        try {
                            emailTemplateService.sendMaintenanceRefundNotice(
                                    booking,
                                    pitch,
                                    req.getStartAt(),
                                    req.getEndAt(),
                                    req.getReason()
                            );
                        } catch (Exception e) {
                            log.error(
                                    "❌ Lỗi khi gửi mail async cho booking {}: {}",
                                    booking.getId(),
                                    e.getMessage()
                            );
                        }
                    });
                }
            });
        }

        return response;
    }

    private void validateMaintenanceTime(MaintenanceWindowRequest req) {
        if (req.getStartAt() == null || req.getEndAt() == null) {
            throw new ApiException(ErrorCode.INVALID_MAINTENANCE_TIME);
        }

        if (!req.getStartAt().isBefore(req.getEndAt())) {
            throw new ApiException(ErrorCode.INVALID_MAINTENANCE_TIME);
        }

        OffsetDateTime now = OffsetDateTime.now();

        if (req.getStartAt().isBefore(now) || req.getEndAt().isBefore(now)) {
            throw new ApiException(ErrorCode.MAINTENANCE_TIME_IN_PAST);
        }
    }

    @Override
    public List<BookingOverlapResponse> checkOverlap(UUID pitchId, OffsetDateTime startAt, OffsetDateTime endAt) {
        var overlappedSlots = bookingSlotRepo.findOverlappedSlots(pitchId, startAt, endAt);

        return overlappedSlots.stream()
                .map(slot -> BookingOverlapResponse.builder()
                        .bookingId(slot.getBooking().getId())
                        .userName(slot.getBooking().getUser().getFullName())
                        .startAt(slot.getStartAt())
                        .endAt(slot.getEndAt())
                        .status(slot.getBooking().getStatus().name())
                        .build())
                .toList();
    }
}