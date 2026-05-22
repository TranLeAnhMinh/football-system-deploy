package com.example.footballmanagement.service.impl;

import java.math.BigDecimal;
import java.util.List;
import java.util.UUID;

import org.springframework.security.access.AccessDeniedException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.example.footballmanagement.entity.User;
import com.example.footballmanagement.entity.Voucher;
import com.example.footballmanagement.entity.enums.UserRole;
import com.example.footballmanagement.entity.enums.VoucherType;
import com.example.footballmanagement.exception.ErrorCode;
import com.example.footballmanagement.exception.custom.VoucherException;
import com.example.footballmanagement.repository.UserRepository;
import com.example.footballmanagement.repository.VoucherRepository;
import com.example.footballmanagement.service.AdminVoucherService;

import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
@Transactional
public class AdminVoucherServiceImpl implements AdminVoucherService {

    private final VoucherRepository voucherRepo;
    private final UserRepository userRepo;

    @Override
    public Voucher createVoucher(Voucher voucher, UUID currentUserId) {

        /* ================= LOAD USER ================= */
        User currentUser = userRepo.findById(currentUserId)
                .orElseThrow(() -> new VoucherException(ErrorCode.USER_NOT_FOUND));

        /* ================= ROLE CHECK ================= */
        if (currentUser.getRole() != UserRole.ADMIN_SYSTEM) {
            throw new AccessDeniedException("Only ADMIN_SYSTEM can create vouchers");
        }

        /* ================= BUSINESS VALIDATION ================= */
        validateVoucherPayload(voucher);

        if (voucherRepo.existsByCode(voucher.getCode())) {
            throw new VoucherException(ErrorCode.VOUCHER_CODE_EXISTS);
        }

        /* ================= DEFAULT FIELDS ================= */
        voucher.setActive(true);

        return voucherRepo.save(voucher);
    }

    /**
     * Kiểm tra toàn bộ ràng buộc nghiệp vụ của 1 voucher trước khi lưu.
     * Tách riêng để tái sử dụng cho create/update sau này.
     */
    private void validateVoucherPayload(Voucher voucher) {
        // 1) Field bắt buộc
        if (voucher.getCode() == null || voucher.getCode().isBlank()) {
            throw new VoucherException(ErrorCode.VOUCHER_CODE_REQUIRED);
        }
        if (voucher.getType() == null) {
            throw new VoucherException(ErrorCode.VOUCHER_TYPE_REQUIRED);
        }
        if (voucher.getValue() == null) {
            throw new VoucherException(ErrorCode.VOUCHER_VALUE_REQUIRED);
        }

        // 2) value phải > 0 (cấm âm và 0 — voucher giá trị 0 vô nghĩa
        //    và voucher giá trị âm sẽ LÀM TĂNG giá khi áp vào booking)
        if (voucher.getValue().compareTo(BigDecimal.ZERO) <= 0) {
            throw new VoucherException(ErrorCode.VOUCHER_VALUE_NOT_POSITIVE);
        }

        // 3) PERCENT: 1 <= value <= 100 (so sánh BigDecimal, không dùng intValue
        //    vì 100.5 sẽ bị truncate thành 100 và lọt qua)
        if (voucher.getType() == VoucherType.PERCENT
                && voucher.getValue().compareTo(BigDecimal.valueOf(100)) > 0) {
            throw new VoucherException(ErrorCode.VOUCHER_PERCENT_INVALID);
        }

        // 4) maxDiscount không được âm (null = không giới hạn, OK)
        if (voucher.getMaxDiscount() != null
                && voucher.getMaxDiscount().compareTo(BigDecimal.ZERO) < 0) {
            throw new VoucherException(ErrorCode.VOUCHER_MAX_DISCOUNT_NEGATIVE);
        }

        // 5) minOrder không được âm
        if (voucher.getMinOrder() != null
                && voucher.getMinOrder().compareTo(BigDecimal.ZERO) < 0) {
            throw new VoucherException(ErrorCode.VOUCHER_MIN_ORDER_NEGATIVE);
        }

        // 6) perUserLimit nếu có phải >= 1
        if (voucher.getPerUserLimit() != null && voucher.getPerUserLimit() < 1) {
            throw new VoucherException(ErrorCode.VOUCHER_PER_USER_LIMIT_INVALID);
        }

        // 7) Khoảng thời gian: start phải TRƯỚC end (không cho phép bằng)
        if (voucher.getStartAt() != null && voucher.getEndAt() != null
                && !voucher.getStartAt().isBefore(voucher.getEndAt())) {
            throw new VoucherException(ErrorCode.VOUCHER_INVALID_TIME);
        }
    }
    @Override
public void deleteVoucher(UUID voucherId, UUID currentUserId) {

    /* ================= LOAD USER ================= */
    User currentUser = userRepo.findById(currentUserId)
            .orElseThrow(() -> new VoucherException(ErrorCode.USER_NOT_FOUND));

    /* ================= ROLE CHECK ================= */
    if (currentUser.getRole() != UserRole.ADMIN_SYSTEM) {
        throw new AccessDeniedException("Only ADMIN_SYSTEM can delete vouchers");
    }

    /* ================= LOAD VOUCHER ================= */
    Voucher voucher = voucherRepo.findById(voucherId)
            .orElseThrow(() -> new VoucherException(ErrorCode.VOUCHER_NOT_FOUND));

    /* ================= BUSINESS VALIDATION ================= */

    // ❌ Đã inactive rồi
    if (!voucher.isActive()) {
        throw new VoucherException(ErrorCode.VOUCHER_ALREADY_INACTIVE);
    }

    // ⚠️ Nếu sau này có voucher_usage thì check ở đây
    // long usageCount = voucherUsageRepo.countByVoucherId(voucherId);
    // if (usageCount > 0) throw new VoucherException(ErrorCode.VOUCHER_ALREADY_USED);

    /* ================= SOFT DELETE ================= */
    voucher.setActive(false);

    voucherRepo.save(voucher);
}
@Override
@Transactional(readOnly = true)
public List<Voucher> getAllVouchers(UUID currentUserId) {

    /* ================= LOAD USER ================= */
    User currentUser = userRepo.findById(currentUserId)
            .orElseThrow(() -> new VoucherException(ErrorCode.USER_NOT_FOUND));

    /* ================= ROLE CHECK ================= */
    if (currentUser.getRole() != UserRole.ADMIN_SYSTEM) {
        throw new AccessDeniedException("Only ADMIN_SYSTEM can view all vouchers");
    }

    /* ================= QUERY ================= */
    return voucherRepo.findAllByOrderByCreatedAtDesc();
}
}

