package com.example.footballmanagement.controller.api;

import java.util.List;
import java.util.UUID;

import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.example.footballmanagement.config.JwtUserDetails;
import com.example.footballmanagement.constant.Endpoint;
import com.example.footballmanagement.entity.Voucher;
import com.example.footballmanagement.service.AdminVoucherService;

import lombok.RequiredArgsConstructor;

@RestController
@RequestMapping(Endpoint.VOUCHER_ADMIN_SYSTEM_API_BASE)
@RequiredArgsConstructor
public class AdminVoucherController {

    private final AdminVoucherService adminVoucherService;

    @PostMapping
    public ResponseEntity<Voucher> createVoucher(
            @RequestBody Voucher voucher,
            @AuthenticationPrincipal JwtUserDetails userDetails
    ) {
        UUID userId = userDetails.getId();
        Voucher created = adminVoucherService.createVoucher(voucher, userId);
        return ResponseEntity.ok(created);
    }

    @GetMapping
    public ResponseEntity<List<Voucher>> getAllVouchers(
            @AuthenticationPrincipal JwtUserDetails userDetails
    ) {
        UUID userId = userDetails.getId();
        List<Voucher> vouchers = adminVoucherService.getAllVouchers(userId);
        return ResponseEntity.ok(vouchers);
    }

    @PutMapping("/{voucherId}")
    public ResponseEntity<Voucher> updateVoucher(
            @PathVariable UUID voucherId,
            @RequestBody Voucher voucher,
            @AuthenticationPrincipal JwtUserDetails userDetails
    ) {
        UUID userId = userDetails.getId();
        Voucher updated = adminVoucherService.updateVoucher(voucherId, voucher, userId);
        return ResponseEntity.ok(updated);
    }

    @PostMapping("/{voucherId}/toggle-active")
    public ResponseEntity<Void> toggleVoucherActive(
            @PathVariable UUID voucherId,
            @AuthenticationPrincipal JwtUserDetails userDetails
    ) {
        UUID userId = userDetails.getId();
        adminVoucherService.toggleVoucherActive(voucherId, userId);
        return ResponseEntity.ok().build();
    }

    @DeleteMapping("/{voucherId}/hard")
    public ResponseEntity<Void> hardDeleteVoucher(
            @PathVariable UUID voucherId,
            @AuthenticationPrincipal JwtUserDetails userDetails
    ) {
        UUID userId = userDetails.getId();
        adminVoucherService.hardDeleteVoucher(voucherId, userId);
        return ResponseEntity.ok().build();
    }
}