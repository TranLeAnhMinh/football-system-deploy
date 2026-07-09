package com.example.footballmanagement.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.security.web.csrf.CookieCsrfTokenRepository;
import org.springframework.security.web.csrf.CsrfFilter;
import org.springframework.security.web.csrf.CsrfTokenRequestAttributeHandler;

import static com.example.footballmanagement.constant.Endpoint.ADMIN_ENDPOINT;
import static com.example.footballmanagement.constant.Endpoint.AUTH_LOGIN;
import static com.example.footballmanagement.constant.Endpoint.AUTH_LOGOUT;
import static com.example.footballmanagement.constant.Endpoint.AUTH_RECOVERY;
import static com.example.footballmanagement.constant.Endpoint.AUTH_RECOVERY_CONFIRM;
import static com.example.footballmanagement.constant.Endpoint.AUTH_REFRESH;
import static com.example.footballmanagement.constant.Endpoint.AUTH_REGISTER;
import static com.example.footballmanagement.constant.Endpoint.BASE_PRICE_ADMIN_SYSTEM_ENDPOINT;
import static com.example.footballmanagement.constant.Endpoint.BOOKING_ADMIN_ENDPOINT;
import static com.example.footballmanagement.constant.Endpoint.BOOKING_BRANCH_ENDPOINT;
import static com.example.footballmanagement.constant.Endpoint.BOOKING_ENDPOINT;
import static com.example.footballmanagement.constant.Endpoint.BOOKING_SLOT_ENDPOINT;
import static com.example.footballmanagement.constant.Endpoint.BRANCH_ADMIN_SYSTEM_ENDPOINT;
import static com.example.footballmanagement.constant.Endpoint.FORGOTPASSWORD_PAGE;
import static com.example.footballmanagement.constant.Endpoint.LOGIN_PAGE;
import static com.example.footballmanagement.constant.Endpoint.MAINTENANCE_WINDOW_ENDPOINT;
import static com.example.footballmanagement.constant.Endpoint.PAYMENT_RETURN;
import static com.example.footballmanagement.constant.Endpoint.PAYMENT_IPN;
import static com.example.footballmanagement.constant.Endpoint.PITCH_ADMIN_ENDPOINT;
import static com.example.footballmanagement.constant.Endpoint.PITCH_ADMIN_SYSTEM_ENDPOINT;
import static com.example.footballmanagement.constant.Endpoint.PITCH_DETAIL_PAGE;
import static com.example.footballmanagement.constant.Endpoint.PITCH_ENDPOINT;
import static com.example.footballmanagement.constant.Endpoint.REGISTER_PAGE;
import static com.example.footballmanagement.constant.Endpoint.RESETPASSWORD_PAGE;
import static com.example.footballmanagement.constant.Endpoint.REVENUE_ADMIN_SYSTEM_ENDPOINT;
import static com.example.footballmanagement.constant.Endpoint.REVENUE_BRANCH_ENDPOINT;
import static com.example.footballmanagement.constant.Endpoint.USER_ADMIN_SYSTEM_ENDPOINT;
import static com.example.footballmanagement.constant.Endpoint.VOUCHER_ADMIN_ENDPOINT;
import static com.example.footballmanagement.constant.Endpoint.VOUCHER_ADMIN_SYSTEM_ENDPOINT;
import static com.example.footballmanagement.constant.Endpoint.VOUCHER_ENDPOINT;

import lombok.RequiredArgsConstructor;

@Configuration
@RequiredArgsConstructor
public class SecurityConfig {

    private final JwtAuthFilter jwtAuthFilter;
    private final CsrfCookieFilter csrfCookieFilter;
    private final RateLimitFilter rateLimitFilter;

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            .headers(headers -> headers
                .contentSecurityPolicy(csp -> csp.policyDirectives(
                    "default-src 'self'; " +
                    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; " +
                    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; " +
                    "font-src 'self' https://cdnjs.cloudflare.com https://fonts.gstatic.com data:; " +
                    "img-src 'self' data: blob: https://res.cloudinary.com; " +
                    "connect-src 'self' http://localhost:5005; " +
                    "object-src 'none'; " +
                    "base-uri 'self'; " +
                    "frame-ancestors 'self'; " +
                    "form-action 'self' https://sandbox.vnpayment.vn https://*.vnpayment.vn; " +
                    "navigate-to 'self' https://sandbox.vnpayment.vn https://*.vnpayment.vn"
                ))
                .frameOptions(frame -> frame.sameOrigin())
                .referrerPolicy(referrer -> referrer.policy(
                    org.springframework.security.web.header.writers.ReferrerPolicyHeaderWriter.ReferrerPolicy.STRICT_ORIGIN_WHEN_CROSS_ORIGIN
                ))
            )
            .csrf(csrf -> csrf
                .csrfTokenRepository(CookieCsrfTokenRepository.withHttpOnlyFalse())
                .csrfTokenRequestHandler(new CsrfTokenRequestAttributeHandler())
                .ignoringRequestMatchers(
                    AUTH_LOGIN,
                    AUTH_REGISTER,
                    AUTH_RECOVERY,
                    AUTH_RECOVERY_CONFIRM,
                    PAYMENT_RETURN,
                    PAYMENT_IPN
                )
            )
            .authorizeHttpRequests(auth -> auth
                /* ========= STATIC & PUBLIC ========= */
                .requestMatchers(
                        AUTH_LOGIN,
                        AUTH_REGISTER,
                        "/api/auth/csrf",
                        LOGIN_PAGE,
                        REGISTER_PAGE,
                        AUTH_REFRESH,
                        AUTH_LOGOUT,
                        AUTH_RECOVERY,
                        AUTH_RECOVERY_CONFIRM,
                        FORGOTPASSWORD_PAGE,
                        RESETPASSWORD_PAGE,
                        PITCH_ENDPOINT,
                        PITCH_DETAIL_PAGE,
                        MAINTENANCE_WINDOW_ENDPOINT,
                        BOOKING_SLOT_ENDPOINT,
                        PAYMENT_RETURN,
                        PAYMENT_IPN,
                        "/css/**",
                        "/js/**",
                        "/images/**",
                        "/webjars/**",
                        "/favicon.ico",
                        "/fonts/**"
                ).permitAll()

                .requestMatchers(HttpMethod.GET, "/api/pitches/*/reviews/**").permitAll()
                .requestMatchers(HttpMethod.POST, "/api/pitches/*/reviews/**").hasRole("USER")
                .requestMatchers("/api/chatbot/**").permitAll()
                /* ========= PUBLIC USER PAGES ========= */
                .requestMatchers("/user/**", "/user/**?lang=**").permitAll()

                /* ========= PUBLIC ADMIN BRANCH PAGES ========= */
                // 👉 Những trang HTML render từ Thymeleaf (chỉ hiển thị giao diện)
                .requestMatchers(
                    "/admin/home",
                    "/admin/home?lang=**",
                    "/adminsystem/home?lang=**",
                    "/admin/maintenance/**",
                    "/admin/bookings",
                    "/admin/bookings/**",
                    "/admin/revenue",
                    "/adminsystem/home",
                    "/admin/revenue/**",
                    "/adminsystem/branches",
                    "/adminsystem/branches?lang=**",
                    "/adminsystem/pitches/**",
                    "/adminsystem/pitches/**?lang=**",
                    "/adminsystem/vouchers",
                    "/adminsystem/vouchers?lang=**",
                    "/adminsystem/users",
                    "/adminsystem/users?lang=**"
                ).permitAll()

                /* ========= API ========= */
                .requestMatchers("/payments/**").hasRole("USER")
                .requestMatchers("/api/payment/**").hasRole("USER")

                /* ========= ADMIN SYSTEM ========= */
                // .requestMatchers(ADMIN_SYSTEM_ENDPOINT).hasRole("ADMIN_SYSTEM")
                .requestMatchers(VOUCHER_ADMIN_ENDPOINT).hasRole("ADMIN_SYSTEM")
                .requestMatchers(ADMIN_ENDPOINT).hasRole("ADMIN_BRANCH")
                .requestMatchers(PITCH_ADMIN_SYSTEM_ENDPOINT).hasRole("ADMIN_SYSTEM")
                .requestMatchers(BRANCH_ADMIN_SYSTEM_ENDPOINT).hasRole("ADMIN_SYSTEM")
                .requestMatchers("/api/adminsystem/images/**").hasRole("ADMIN_SYSTEM")
                .requestMatchers("/api/adminsystem/payments/**").hasRole("ADMIN_SYSTEM")
                .requestMatchers(VOUCHER_ADMIN_SYSTEM_ENDPOINT).hasRole("ADMIN_SYSTEM")
                .requestMatchers(REVENUE_ADMIN_SYSTEM_ENDPOINT).hasRole("ADMIN_SYSTEM")
                .requestMatchers(USER_ADMIN_SYSTEM_ENDPOINT).hasRole("ADMIN_SYSTEM") 
                .requestMatchers(BASE_PRICE_ADMIN_SYSTEM_ENDPOINT).hasRole("ADMIN_SYSTEM")


                /* ========= ADMIN BRANCH API ========= */
                .requestMatchers(PITCH_ADMIN_ENDPOINT).hasRole("ADMIN_BRANCH")
                .requestMatchers(BOOKING_BRANCH_ENDPOINT).hasRole("ADMIN_BRANCH")
                .requestMatchers(BOOKING_ADMIN_ENDPOINT).hasRole("ADMIN_BRANCH")
                .requestMatchers(REVENUE_BRANCH_ENDPOINT).hasRole("ADMIN_BRANCH")
                .requestMatchers("/api/admin/maintenance-windows/**").hasRole("ADMIN_BRANCH")

                /* ========= USER API ========= */
                .requestMatchers(BOOKING_ENDPOINT).hasRole("USER")
                .requestMatchers(VOUCHER_ENDPOINT).hasRole("USER")

        

                /* ========= ALL OTHER ========= */
                .anyRequest().authenticated()
            )

            /* ========= Session Stateless ========= */
            .sessionManagement(session ->
                session.sessionCreationPolicy(SessionCreationPolicy.STATELESS)
            )

            /* ========= JWT Filter ========= */
            .addFilterBefore(rateLimitFilter, CsrfFilter.class)
            .addFilterAfter(csrfCookieFilter, CsrfFilter.class)
            .addFilterBefore(jwtAuthFilter, UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }
}
