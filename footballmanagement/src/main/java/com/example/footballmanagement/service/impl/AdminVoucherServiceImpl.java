package com.example.footballmanagement.service.impl;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
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
        User currentUser = userRepo.findById(currentUserId)
                .orElseThrow(() -> new VoucherException(ErrorCode.USER_NOT_FOUND));

        if (currentUser.getRole() != UserRole.ADMIN_SYSTEM) {
            throw new AccessDeniedException("Only ADMIN_SYSTEM can create vouchers");
        }

        validateVoucherPayload(voucher);
        validateCreateTime(voucher);

        if (voucherRepo.existsByCode(voucher.getCode())) {
            throw new VoucherException(ErrorCode.VOUCHER_CODE_EXISTS);
        }

        voucher.setActive(true);

        return voucherRepo.save(voucher);
    }

    @Override
    public void toggleVoucherActive(UUID voucherId, UUID currentUserId) {
        User currentUser = userRepo.findById(currentUserId)
                .orElseThrow(() -> new VoucherException(ErrorCode.USER_NOT_FOUND));

        if (currentUser.getRole() != UserRole.ADMIN_SYSTEM) {
            throw new AccessDeniedException("Only ADMIN_SYSTEM can update voucher status");
        }

        Voucher voucher = voucherRepo.findById(voucherId)
                .orElseThrow(() -> new VoucherException(ErrorCode.VOUCHER_NOT_FOUND));

        if (isExpired(voucher)) {
            voucher.setActive(false);
        } else {
            voucher.setActive(!voucher.isActive());
        }

        voucherRepo.save(voucher);
    }

    @Override
    public List<Voucher> getAllVouchers(UUID currentUserId) {
        User currentUser = userRepo.findById(currentUserId)
                .orElseThrow(() -> new VoucherException(ErrorCode.USER_NOT_FOUND));

        if (currentUser.getRole() != UserRole.ADMIN_SYSTEM) {
            throw new AccessDeniedException("Only ADMIN_SYSTEM can view all vouchers");
        }

        voucherRepo.deactivateExpiredVouchers(OffsetDateTime.now());

        return voucherRepo.findAllByOrderByCreatedAtDesc();
    }

    @Override
    public void hardDeleteVoucher(UUID voucherId, UUID currentUserId) {
        User currentUser = userRepo.findById(currentUserId)
                .orElseThrow(() -> new VoucherException(ErrorCode.USER_NOT_FOUND));

        if (currentUser.getRole() != UserRole.ADMIN_SYSTEM) {
            throw new AccessDeniedException("Only ADMIN_SYSTEM can hard delete vouchers");
        }

        Voucher voucher = voucherRepo.findById(voucherId)
                .orElseThrow(() -> new VoucherException(ErrorCode.VOUCHER_NOT_FOUND));

        voucherRepo.delete(voucher);
    }

    @Override
    public Voucher updateVoucher(UUID voucherId, Voucher request, UUID currentUserId) {
        User currentUser = userRepo.findById(currentUserId)
                .orElseThrow(() -> new VoucherException(ErrorCode.USER_NOT_FOUND));

        if (currentUser.getRole() != UserRole.ADMIN_SYSTEM) {
            throw new AccessDeniedException("Only ADMIN_SYSTEM can update vouchers");
        }

        Voucher voucher = voucherRepo.findById(voucherId)
                .orElseThrow(() -> new VoucherException(ErrorCode.VOUCHER_NOT_FOUND));

        OffsetDateTime oldStartAt = voucher.getStartAt();

        voucher.setCode(request.getCode());
        voucher.setType(request.getType());
        voucher.setValue(request.getValue());
        voucher.setMinOrder(request.getMinOrder());
        voucher.setMaxDiscount(request.getMaxDiscount());
        voucher.setStartAt(request.getStartAt());
        voucher.setEndAt(request.getEndAt());
        voucher.setPerUserLimit(request.getPerUserLimit());

        validateVoucherPayload(voucher);
        validateUpdateTime(oldStartAt, voucher);

        if (voucherRepo.existsByCodeAndIdNot(voucher.getCode(), voucherId)) {
            throw new VoucherException(ErrorCode.VOUCHER_CODE_EXISTS);
        }

        voucher.setActive(!isExpired(voucher));

        return voucherRepo.save(voucher);
    }

    private boolean isExpired(Voucher voucher) {
        return voucher.getEndAt() != null
                && voucher.getEndAt().isBefore(OffsetDateTime.now());
    }

    private void validateCreateTime(Voucher voucher) {
        OffsetDateTime now = OffsetDateTime.now();

        if (voucher.getStartAt() != null && voucher.getStartAt().isBefore(now)) {
            throw new VoucherException(ErrorCode.VOUCHER_INVALID_TIME);
        }

        if (voucher.getEndAt() != null && voucher.getEndAt().isBefore(now)) {
            throw new VoucherException(ErrorCode.VOUCHER_INVALID_TIME);
        }
    }

    private void validateUpdateTime(OffsetDateTime oldStartAt, Voucher voucher) {
        OffsetDateTime now = OffsetDateTime.now();

        boolean voucherAlreadyStarted =
                oldStartAt != null && oldStartAt.isBefore(now);

        if (voucherAlreadyStarted && !oldStartAt.equals(voucher.getStartAt())) {
            throw new VoucherException(ErrorCode.VOUCHER_INVALID_TIME);
        }
    }

    private void validateVoucherPayload(Voucher voucher) {
        if (voucher.getCode() == null || voucher.getCode().isBlank()) {
            throw new VoucherException(ErrorCode.VOUCHER_CODE_REQUIRED);
        }

        if (voucher.getType() == null) {
            throw new VoucherException(ErrorCode.VOUCHER_TYPE_REQUIRED);
        }

        if (voucher.getValue() == null) {
            throw new VoucherException(ErrorCode.VOUCHER_VALUE_REQUIRED);
        }

        if (voucher.getValue().compareTo(BigDecimal.ZERO) <= 0) {
            throw new VoucherException(ErrorCode.VOUCHER_VALUE_NOT_POSITIVE);
        }

        if (voucher.getType() == VoucherType.PERCENT
                && voucher.getValue().compareTo(BigDecimal.valueOf(100)) > 0) {
            throw new VoucherException(ErrorCode.VOUCHER_PERCENT_INVALID);
        }

        if (voucher.getMaxDiscount() != null
                && voucher.getMaxDiscount().compareTo(BigDecimal.ZERO) < 0) {
            throw new VoucherException(ErrorCode.VOUCHER_MAX_DISCOUNT_NEGATIVE);
        }

        if (voucher.getMinOrder() != null
                && voucher.getMinOrder().compareTo(BigDecimal.ZERO) < 0) {
            throw new VoucherException(ErrorCode.VOUCHER_MIN_ORDER_NEGATIVE);
        }

        if (voucher.getPerUserLimit() != null && voucher.getPerUserLimit() < 1) {
            throw new VoucherException(ErrorCode.VOUCHER_PER_USER_LIMIT_INVALID);
        }

        if (voucher.getStartAt() != null
                && voucher.getEndAt() != null
                && !voucher.getStartAt().isBefore(voucher.getEndAt())) {
            throw new VoucherException(ErrorCode.VOUCHER_INVALID_TIME);
        }
    }
}