package com.example.footballmanagement.exception;

import org.springframework.http.HttpStatus;

import lombok.Getter;

@Getter
public enum ErrorCode {

    // ===== AUTH / ROLE =====
    ROLE_REQUIRED(HttpStatus.BAD_REQUEST, "Role is required"),
    ROLE_FORBIDDEN(HttpStatus.FORBIDDEN, "You are not allowed to perform this action"),

    // ===== USER =====
    USER_NOT_FOUND(HttpStatus.NOT_FOUND, "Không tìm thấy người dùng"),
    USER_INACTIVE(HttpStatus.FORBIDDEN, "Tài khoản của bạn đang bị vô hiệu hóa"),

    // ===== PITCH / MAINTENANCE =====
    PITCH_NOT_FOUND(HttpStatus.NOT_FOUND, "Không tìm thấy sân bóng"),
    MAINTENANCE_CONFLICT(HttpStatus.CONFLICT, "Khung giờ bảo trì bị trùng"),
    PERMISSION_DENIED(HttpStatus.FORBIDDEN, "Bạn không có quyền thao tác này"),

    // ===== BRANCH =====
    BRANCH_NOT_FOUND(HttpStatus.NOT_FOUND, "Không tìm thấy chi nhánh"),
    MAINTENANCE_NOT_FOUND(HttpStatus.NOT_FOUND, "Không tìm thấy lịch bảo trì"),
    MAINTENANCE_ALREADY_STARTED(HttpStatus.BAD_REQUEST, "Không thể xoá lịch bảo trì đã hoặc đang diễn ra"),

    // ===== VOUCHER (USER FLOW) =====
    VOUCHER_NOT_FOUND(HttpStatus.NOT_FOUND, "Voucher not found"),
    VOUCHER_INACTIVE(HttpStatus.BAD_REQUEST, "Voucher is not active"),
    VOUCHER_NOT_STARTED(HttpStatus.BAD_REQUEST, "Voucher not started yet"),
    VOUCHER_EXPIRED(HttpStatus.BAD_REQUEST, "Voucher expired"),
    VOUCHER_MIN_ORDER(HttpStatus.BAD_REQUEST, "Order does not meet minimum amount for voucher"),
    VOUCHER_LIMIT_REACHED(HttpStatus.BAD_REQUEST, "Voucher usage limit reached for this user"),

    INVALID_BRANCH_NAME(HttpStatus.BAD_REQUEST, "Branch name cannot be empty"),
INVALID_BRANCH_LOCATION(HttpStatus.BAD_REQUEST, "Branch location cannot be empty"),
BRANCH_NAME_ALREADY_EXISTS(HttpStatus.BAD_REQUEST, "Branch name already exists"),
    // ===== VOUCHER (ADMIN FLOW) =====
    // ===== VOUCHER (ADMIN FLOW) =====
VOUCHER_CODE_EXISTS(HttpStatus.CONFLICT, "Voucher code already exists"),
VOUCHER_INVALID_TIME(HttpStatus.BAD_REQUEST, "Voucher start time must be before end time"),
VOUCHER_PERCENT_INVALID(HttpStatus.BAD_REQUEST, "Percent voucher value must be between 1 and 100"),
VOUCHER_VALUE_REQUIRED(HttpStatus.BAD_REQUEST, "Voucher value is required"),
VOUCHER_VALUE_NOT_POSITIVE(HttpStatus.BAD_REQUEST, "Voucher value must be greater than 0"),
VOUCHER_MAX_DISCOUNT_NEGATIVE(HttpStatus.BAD_REQUEST, "Max discount cannot be negative"),
VOUCHER_MIN_ORDER_NEGATIVE(HttpStatus.BAD_REQUEST, "Min order cannot be negative"),
VOUCHER_PER_USER_LIMIT_INVALID(HttpStatus.BAD_REQUEST, "Per-user limit must be at least 1"),
VOUCHER_TYPE_REQUIRED(HttpStatus.BAD_REQUEST, "Voucher type is required"),
VOUCHER_CODE_REQUIRED(HttpStatus.BAD_REQUEST, "Voucher code is required"),
VOUCHER_ALREADY_INACTIVE(HttpStatus.BAD_REQUEST, "Voucher is already inactive"),
ACTION_NOT_ALLOWED(HttpStatus.BAD_REQUEST, "Action is not allowed"),
UPDATE_FAILED(HttpStatus.INTERNAL_SERVER_ERROR, "Update failed"),
BRANCH_ALREADY_HAVE_ADMIN(HttpStatus.BAD_REQUEST, "Branch already has admin"),
BOOKING_TIME_IN_PAST(HttpStatus.BAD_REQUEST, "Không thể đặt sân ở thời gian trong quá khứ"),
INVALID_BOOKING_TIME(HttpStatus.BAD_REQUEST, "Thời gian bắt đầu phải trước thời gian kết thúc"),
MAINTENANCE_TIME_IN_PAST(HttpStatus.BAD_REQUEST, "Không thể tạo lịch bảo trì trong quá khứ"),
INVALID_MAINTENANCE_TIME(HttpStatus.BAD_REQUEST, "Thời gian bắt đầu phải trước thời gian kết thúc"),
BOOKING_SLOT_UNAVAILABLE(HttpStatus.CONFLICT, "Khung giờ này đang không khả dụng"),
PENDING_BOOKING_CONFLICT(HttpStatus.CONFLICT, "Có khách hàng đang giữ chỗ trong khung giờ này"),
VOUCHER_ALREADY_USED(HttpStatus.BAD_REQUEST, "Voucher has already been used and cannot be deleted");



    

    private final HttpStatus status;
    private final String message;

    ErrorCode(HttpStatus status, String message) {
        this.status = status;
        this.message = message;
    }
}
