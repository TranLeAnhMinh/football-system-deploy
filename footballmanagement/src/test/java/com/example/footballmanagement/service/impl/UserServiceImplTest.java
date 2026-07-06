package com.example.footballmanagement.service.impl;

import java.util.Optional;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertThrows;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.password.PasswordEncoder;

import com.example.footballmanagement.entity.User;
import com.example.footballmanagement.entity.enums.UserRole;
import com.example.footballmanagement.exception.ApiException;
import com.example.footballmanagement.repository.BranchRepository;
import com.example.footballmanagement.repository.UserRepository;
import com.example.footballmanagement.service.NotificationService;

@ExtendWith(MockitoExtension.class)
class UserServiceImplTest {

    @Mock
    private UserRepository userRepository;

    @Mock
    private PasswordEncoder passwordEncoder;

    @Mock
    private NotificationService notificationService;

    @Mock
    private BranchRepository branchRepository;

    private UserServiceImpl userService;

    @BeforeEach
    void setUp() {
        userService = new UserServiceImpl(userRepository, passwordEncoder, notificationService, branchRepository);
    }

    @Test
    void toggleUserStatus_shouldSwitchToInactiveForActiveUser() {
        UUID adminId = UUID.randomUUID();
        UUID targetId = UUID.randomUUID();

        User admin = User.builder().id(adminId).role(UserRole.ADMIN_SYSTEM).build();
        User target = User.builder().id(targetId).role(UserRole.USER).build();

        when(userRepository.findById(adminId)).thenReturn(Optional.of(admin));
        when(userRepository.findById(targetId)).thenReturn(Optional.of(target));
        when(userRepository.updateStatus(targetId, com.example.footballmanagement.entity.enums.UserStatus.INACTIVE)).thenReturn(1);

        userService.toggleUserStatus(targetId, adminId);

        verify(userRepository).updateStatus(targetId, com.example.footballmanagement.entity.enums.UserStatus.INACTIVE);
    }

    @Test
    void toggleUserStatus_shouldRejectSelfChange() {
        UUID adminId = UUID.randomUUID();
        User admin = User.builder().id(adminId).role(UserRole.ADMIN_SYSTEM).build();

        when(userRepository.findById(adminId)).thenReturn(Optional.of(admin));

        assertThrows(ApiException.class, () -> userService.toggleUserStatus(adminId, adminId));
    }
}
