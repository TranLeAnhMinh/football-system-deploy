package com.example.footballmanagement.service;

import java.util.List;
import java.util.UUID;

import com.example.footballmanagement.entity.Voucher;

public interface AdminVoucherService {

    // ✅ Chỉ ADMIN_SYSTEM được tạo voucher
    Voucher createVoucher(Voucher voucher, UUID currentUserId);
    // Toggle chuyển
    void toggleVoucherActive(UUID voucherId, UUID currentUserId);

    List<Voucher> getAllVouchers(UUID currentUserId);

    void hardDeleteVoucher(UUID voucherId, UUID currentUserId);
    
    Voucher updateVoucher(UUID voucherId, Voucher voucher, UUID currentUserId);

}
