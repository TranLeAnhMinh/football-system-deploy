package com.example.footballmanagement.config;

import java.io.IOException;
import java.time.Duration;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

@Component
public class RateLimitFilter extends OncePerRequestFilter {

    private final Map<String, WindowCounter> counters = new ConcurrentHashMap<>();

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {
        LimitRule rule = resolveRule(request);

        if (rule != null && !allow(request, rule)) {
            response.setStatus(HttpStatus.TOO_MANY_REQUESTS.value());
            response.setContentType("application/json");
            response.setHeader("Retry-After", String.valueOf(rule.window().toSeconds()));
            response.getWriter().write("{\"message\":\"Too many requests. Please try again later.\"}");
            return;
        }

        chain.doFilter(request, response);
    }

    private boolean allow(HttpServletRequest request, LimitRule rule) {
        long now = System.currentTimeMillis();
        String key = rule.name() + ":" + clientIp(request);

        WindowCounter counter = counters.compute(key, (unused, existing) -> {
            if (existing == null || now >= existing.expiresAt) {
                return new WindowCounter(now + rule.window().toMillis());
            }
            return existing;
        });

        cleanupExpiredCounters(now);
        return counter.count.incrementAndGet() <= rule.maxRequests();
    }

    private LimitRule resolveRule(HttpServletRequest request) {
        String path = request.getRequestURI();

        if ("GET".equalsIgnoreCase(request.getMethod()) && path.equals("/api/payment/vnpay")) {
            return new LimitRule("payment", 20, Duration.ofMinutes(1));
        }

        if (!isUnsafeMethod(request.getMethod())) {
            return null;
        }

        if (path.equals("/api/auth/login")) {
            return new LimitRule("auth-login", 10, Duration.ofMinutes(1));
        }
        if (path.equals("/api/auth/refresh")) {
            return new LimitRule("auth-refresh", 30, Duration.ofMinutes(1));
        }
        if (path.equals("/api/auth/register")) {
            return new LimitRule("auth-register", 5, Duration.ofMinutes(15));
        }
        if (path.equals("/api/auth/recover")) {
            return new LimitRule("auth-recover", 5, Duration.ofMinutes(15));
        }
        if (path.equals("/api/auth/recover/confirm")) {
            return new LimitRule("auth-recover-confirm", 10, Duration.ofMinutes(15));
        }
        if (path.matches("^/api/pitches/[^/]+/reviews/?$")) {
            return new LimitRule("review-write", 10, Duration.ofMinutes(1));
        }
        if (path.equals("/api/bookings")) {
            return new LimitRule("booking-create", 20, Duration.ofMinutes(1));
        }
        if (path.startsWith("/payments/") || path.startsWith("/api/payment/")) {
            return new LimitRule("payment", 20, Duration.ofMinutes(1));
        }
        if (path.startsWith("/api/admin/") || path.startsWith("/api/adminsystem/")) {
            return new LimitRule("admin-write", 120, Duration.ofMinutes(1));
        }

        return null;
    }

    private boolean isUnsafeMethod(String method) {
        return "POST".equalsIgnoreCase(method)
                || "PUT".equalsIgnoreCase(method)
                || "PATCH".equalsIgnoreCase(method)
                || "DELETE".equalsIgnoreCase(method);
    }

    private String clientIp(HttpServletRequest request) {
        String forwardedFor = request.getHeader("X-Forwarded-For");
        if (forwardedFor != null && !forwardedFor.isBlank()) {
            return forwardedFor.split(",")[0].trim();
        }

        String realIp = request.getHeader("X-Real-IP");
        if (realIp != null && !realIp.isBlank()) {
            return realIp.trim();
        }

        return request.getRemoteAddr();
    }

    private void cleanupExpiredCounters(long now) {
        if (counters.size() < 1_000) {
            return;
        }
        counters.entrySet().removeIf(entry -> now >= entry.getValue().expiresAt);
    }

    private record LimitRule(String name, int maxRequests, Duration window) {
    }

    private static class WindowCounter {
        private final AtomicInteger count = new AtomicInteger(0);
        private final long expiresAt;

        private WindowCounter(long expiresAt) {
            this.expiresAt = expiresAt;
        }
    }
}
