package com.example.footballmanagement.dto.response;

import java.math.BigDecimal;

import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class BookingPriceResponse {
    private final BigDecimal basePrice;          // giá gốc
    private final BigDecimal priceRuleDiscount;  // số tiền giảm do PriceRule
    private final BigDecimal voucherDiscount;    // số tiền giảm do voucher
    private final BigDecimal finalPrice;         // giá sau tất cả giảm giá
    private final String currency;               // ví dụ: "VND"
}