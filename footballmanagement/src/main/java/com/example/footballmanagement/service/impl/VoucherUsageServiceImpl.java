package com.example.footballmanagement.service.impl;

import java.math.BigDecimal;
import java.util.UUID;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.example.footballmanagement.entity.Booking;
import com.example.footballmanagement.entity.User;
import com.example.footballmanagement.entity.Voucher;
import com.example.footballmanagement.entity.VoucherUsage;
import com.example.footballmanagement.exception.ErrorCode;
import com.example.footballmanagement.exception.custom.VoucherException;
import com.example.footballmanagement.repository.VoucherRepository;
import com.example.footballmanagement.repository.VoucherUsageRepository;
import com.example.footballmanagement.service.VoucherUsageService;

import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class VoucherUsageServiceImpl implements VoucherUsageService {

    private final VoucherUsageRepository usageRepo;
    private final VoucherRepository voucherRepo;

    @Override
    @Transactional
    public VoucherUsage createUsage(Voucher voucher, User user, Booking booking, BigDecimal discountAmount) {

        Voucher lockedVoucher = voucherRepo.findByIdForUpdate(voucher.getId())
                .orElseThrow(() -> new VoucherException(ErrorCode.VOUCHER_NOT_FOUND));

        if (lockedVoucher.getPerUserLimit() != null) {
            long usedCount = usageRepo.countByUser_IdAndVoucher_Id(user.getId(), lockedVoucher.getId());

            if (usedCount >= lockedVoucher.getPerUserLimit()) {
                throw new VoucherException(ErrorCode.VOUCHER_LIMIT_REACHED);
            }
        }

        VoucherUsage usage = VoucherUsage.builder()
                .voucher(lockedVoucher)
                .user(user)
                .booking(booking)
                .discountAmount(discountAmount)
                .build();

        return usageRepo.save(usage);
    }

    @Override
    public long countUsageByUser(UUID userId, UUID voucherId) {
        return usageRepo.countByUser_IdAndVoucher_Id(userId, voucherId);
    }
}