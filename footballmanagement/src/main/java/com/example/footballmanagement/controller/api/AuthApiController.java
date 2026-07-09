package com.example.footballmanagement.controller.api;

import java.util.Map;

import org.springframework.http.ResponseEntity;
import org.springframework.security.web.csrf.CsrfToken;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.example.footballmanagement.config.JwtCookieService;
import com.example.footballmanagement.dto.request.LoginRequest;
import com.example.footballmanagement.dto.request.RegisterRequest;
import com.example.footballmanagement.dto.response.JwtResponse;
import com.example.footballmanagement.dto.response.RegisterResponse;
import com.example.footballmanagement.service.AuthService;
import com.example.footballmanagement.service.UserService;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;


@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
public class AuthApiController {

    private final UserService userService;
    private final AuthService authService;
    private final JwtCookieService jwtCookieService;

    @PostMapping("/register")
    public ResponseEntity<RegisterResponse> register(@RequestBody RegisterRequest request) {
        return ResponseEntity.ok(userService.register(request));
    }

    @GetMapping("/csrf")
    public ResponseEntity<Map<String, String>> csrf(CsrfToken csrfToken) {
        return ResponseEntity.ok(Map.of(
                "token", csrfToken.getToken(),
                "headerName", csrfToken.getHeaderName(),
                "parameterName", csrfToken.getParameterName()
        ));
    }

    @PostMapping("/login")
    public ResponseEntity<JwtResponse> login(@Valid @RequestBody LoginRequest req,
                                             HttpServletRequest http,
                                             HttpServletResponse response) {
        JwtResponse jwtResponse = authService.login(req, http);
        jwtCookieService.addAuthCookies(http, response, jwtResponse.getAccessToken(), jwtResponse.getRefreshToken());
        return ResponseEntity.ok(jwtResponse);
    }

    @PostMapping("/refresh")
    public ResponseEntity<JwtResponse> refresh(HttpServletRequest request, HttpServletResponse response) {
        String refreshToken = jwtCookieService.getRefreshToken(request);
        if (refreshToken == null || refreshToken.isBlank()) {
            return ResponseEntity.status(401).build();
        }
        JwtResponse jwtResponse = authService.refresh(refreshToken);
        jwtCookieService.addAuthCookies(request, response, jwtResponse.getAccessToken(), jwtResponse.getRefreshToken());
        return ResponseEntity.ok(jwtResponse);
    }

    @PostMapping("/logout")
    public ResponseEntity<Void> logout(HttpServletRequest request, HttpServletResponse response) {
        String token = jwtCookieService.getAccessToken(request);
        if (token != null) authService.logout(token);
        jwtCookieService.clearAuthCookies(request, response);
        return ResponseEntity.noContent().build();
    }
    
}
