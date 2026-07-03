package com.example.footballmanagement.dto.request;

import java.time.OffsetDateTime;
import java.util.UUID;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ChatbotAvailabilityRequest {
    private UUID pitchId;
    private UUID branchId;
    private OffsetDateTime startAt;
    private OffsetDateTime endAt;
}
