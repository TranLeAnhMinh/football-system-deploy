package com.example.footballmanagement.dto.response;

import java.util.UUID;

import com.fasterxml.jackson.annotation.JsonIgnore;

import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class JwtResponse{
    @JsonIgnore
    private final String accessToken;
    @JsonIgnore
    private final String refreshToken;
    private final UUID userId;
    private final String fullName;
    private final String role;
}
