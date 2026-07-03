package com.example.footballmanagement.dto.response;

import java.util.List;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ChatbotAvailabilityResponse {
    private boolean available;
    private String message;
    private List<String> conflicts;
}
