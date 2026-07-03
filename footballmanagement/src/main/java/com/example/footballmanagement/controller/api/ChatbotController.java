package com.example.footballmanagement.controller.api;

import java.util.List;
import java.util.UUID;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.example.footballmanagement.dto.request.ChatbotAvailabilityRequest;
import com.example.footballmanagement.dto.response.ChatbotAvailabilityResponse;
import com.example.footballmanagement.dto.response.ChatbotBranchResponse;
import com.example.footballmanagement.dto.response.ChatbotPitchResponse;
import com.example.footballmanagement.entity.Branch;
import com.example.footballmanagement.entity.Pitch;
import com.example.footballmanagement.repository.BookingSlotRepository;
import com.example.footballmanagement.repository.BranchRepository;
import com.example.footballmanagement.repository.MaintenanceWindowRepository;
import com.example.footballmanagement.repository.PitchRepository;

import lombok.RequiredArgsConstructor;

@RestController
@RequestMapping("/api/chatbot")
@RequiredArgsConstructor
public class ChatbotController {

    private final BranchRepository branchRepository;
    private final PitchRepository pitchRepository;
    private final BookingSlotRepository bookingSlotRepository;
    private final MaintenanceWindowRepository maintenanceWindowRepository;

    @GetMapping("/branches")
    public ResponseEntity<List<ChatbotBranchResponse>> getBranches() {
        List<ChatbotBranchResponse> response = branchRepository.findAll().stream()
                .filter(Branch::isActive)
                .map(branch -> ChatbotBranchResponse.builder()
                        .id(branch.getId())
                        .name(branch.getName())
                        .location(branch.getLocation())
                        .build())
                .toList();

        return ResponseEntity.ok(response);
    }

    @GetMapping("/pitches")
    public ResponseEntity<List<ChatbotPitchResponse>> getPitches(@RequestParam(required = false) UUID branchId) {
        List<Pitch> pitches;

        if (branchId != null) {
            pitches = pitchRepository.findByBranch_Id(branchId);
        } else {
            pitches = pitchRepository.findByActiveTrue();
        }

        List<ChatbotPitchResponse> response = pitches.stream()
                .filter(Pitch::isActive)
                .map(pitch -> ChatbotPitchResponse.builder()
                        .id(pitch.getId())
                        .name(pitch.getName())
                        .location(pitch.getLocation())
                        .branchId(pitch.getBranch() != null ? pitch.getBranch().getId() : null)
                        .branchName(pitch.getBranch() != null ? pitch.getBranch().getName() : null)
                        .build())
                .toList();

        return ResponseEntity.ok(response);
    }

    @PostMapping("/availability/check")
    public ResponseEntity<ChatbotAvailabilityResponse> checkAvailability(@RequestBody ChatbotAvailabilityRequest request) {
        if (request.getPitchId() == null || request.getStartAt() == null || request.getEndAt() == null) {
            return ResponseEntity.badRequest().body(ChatbotAvailabilityResponse.builder()
                    .available(false)
                    .message("Thiếu thông tin pitchId/startAt/endAt")
                    .conflicts(List.of())
                    .build());
        }

        boolean hasBookingConflict = bookingSlotRepository.existsOverlap(request.getPitchId(), request.getStartAt(), request.getEndAt());
        boolean hasMaintenanceConflict = maintenanceWindowRepository.existsOverlap(request.getPitchId(), request.getStartAt(), request.getEndAt());

        boolean available = !hasBookingConflict && !hasMaintenanceConflict;

        List<String> conflicts = new java.util.ArrayList<>();
        if (hasBookingConflict) {
            conflicts.add("booking");
        }
        if (hasMaintenanceConflict) {
            conflicts.add("maintenance");
        }

        return ResponseEntity.ok(ChatbotAvailabilityResponse.builder()
                .available(available)
                .message(available ? "Sân còn trống" : "Sân đã bị đặt hoặc đang bảo trì")
                .conflicts(conflicts)
                .build());
    }
}
