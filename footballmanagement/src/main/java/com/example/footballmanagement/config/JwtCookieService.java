package com.example.footballmanagement.config;

import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseCookie;
import org.springframework.stereotype.Service;

import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class JwtCookieService {

    public static final String ACCESS_TOKEN_COOKIE = "ACCESS_TOKEN";
    public static final String REFRESH_TOKEN_COOKIE = "REFRESH_TOKEN";

    private final JwtProperties jwtProperties;

    public String getAccessToken(HttpServletRequest request) {
        return getCookieValue(request, ACCESS_TOKEN_COOKIE);
    }

    public String getRefreshToken(HttpServletRequest request) {
        return getCookieValue(request, REFRESH_TOKEN_COOKIE);
    }

    public void addAuthCookies(HttpServletRequest request, HttpServletResponse response,
                               String accessToken, String refreshToken) {
        response.addHeader(HttpHeaders.SET_COOKIE, buildCookie(
                request,
                ACCESS_TOKEN_COOKIE,
                accessToken,
                "/",
                jwtProperties.getAccessExpMs() / 1000
        ).toString());
        response.addHeader(HttpHeaders.SET_COOKIE, buildCookie(
                request,
                REFRESH_TOKEN_COOKIE,
                refreshToken,
                "/api/auth",
                jwtProperties.getRefreshExpMs() / 1000
        ).toString());
    }

    public void clearAuthCookies(HttpServletRequest request, HttpServletResponse response) {
        response.addHeader(HttpHeaders.SET_COOKIE, buildCookie(
                request,
                ACCESS_TOKEN_COOKIE,
                "",
                "/",
                0
        ).toString());
        response.addHeader(HttpHeaders.SET_COOKIE, buildCookie(
                request,
                REFRESH_TOKEN_COOKIE,
                "",
                "/api/auth",
                0
        ).toString());
    }

    private ResponseCookie buildCookie(HttpServletRequest request, String name, String value,
                                       String path, long maxAgeSeconds) {
        return ResponseCookie.from(name, value)
                .httpOnly(true)
                .secure(isSecureRequest(request))
                .sameSite("Lax")
                .path(path)
                .maxAge(maxAgeSeconds)
                .build();
    }

    private boolean isSecureRequest(HttpServletRequest request) {
        return request.isSecure() || "https".equalsIgnoreCase(request.getHeader("X-Forwarded-Proto"));
    }

    private String getCookieValue(HttpServletRequest request, String name) {
        Cookie[] cookies = request.getCookies();
        if (cookies == null) {
            return null;
        }
        for (Cookie cookie : cookies) {
            if (name.equals(cookie.getName())) {
                return cookie.getValue();
            }
        }
        return null;
    }
}
