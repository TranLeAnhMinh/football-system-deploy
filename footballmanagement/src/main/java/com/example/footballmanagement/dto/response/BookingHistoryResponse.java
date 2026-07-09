package com.example.footballmanagement.dto.response;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;

import com.example.footballmanagement.entity.enums.BookingStatus;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class BookingHistoryResponse {
    private UUID bookingId;
    private String pitchName;
    private String branchName;
    private BookingStatus status;
    private OffsetDateTime createdAt;
    private BigDecimal finalPrice;
    private PaymentInfoResponse payment;
    private List<SlotResponse> slots;

    @Data
    @Builder
    public static class SlotResponse {
        private OffsetDateTime startAt;
        private OffsetDateTime endAt;
        private boolean checkedIn; // true nếu checked_in_at != null
    }
}
