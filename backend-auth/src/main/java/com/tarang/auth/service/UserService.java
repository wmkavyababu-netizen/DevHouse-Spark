package com.tarang.auth.service;

import com.tarang.auth.dto.UserResponse;
import com.tarang.auth.exception.ResourceNotFoundException;
import com.tarang.auth.model.Organization;
import com.tarang.auth.model.Role;
import com.tarang.auth.model.User;
import com.tarang.auth.repository.OrganizationRepository;
import com.tarang.auth.repository.RoleRepository;
import com.tarang.auth.repository.UserRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;
import java.util.stream.Collectors;

@Service
public class UserService {

    private final UserRepository userRepository;
    private final RoleRepository roleRepository;
    private final OrganizationRepository organizationRepository;
    private final AuthService authService;

    public UserService(UserRepository userRepository,
                       RoleRepository roleRepository,
                       OrganizationRepository organizationRepository,
                       AuthService authService) {
        this.userRepository = userRepository;
        this.roleRepository = roleRepository;
        this.organizationRepository = organizationRepository;
        this.authService = authService;
    }

    @Transactional(readOnly = true)
    public Page<UserResponse> listUsers(String status, UUID organizationId, Pageable pageable) {
        return userRepository.findWithFilters(status, organizationId, pageable)
                .map(authService::toUserResponse);
    }

    @Transactional(readOnly = true)
    public UserResponse getUserById(UUID id) {
        User user = userRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("User not found with ID: " + id));
        return authService.toUserResponse(user);
    }

    @Transactional
    public UserResponse updateUserRoles(UUID userId, Set<String> roleNames) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new ResourceNotFoundException("User not found with ID: " + userId));

        Set<Role> roles = new HashSet<>();
        for (String roleName : roleNames) {
            Role role = roleRepository.findByName(roleName.toLowerCase().trim())
                    .orElseThrow(() -> new ResourceNotFoundException("Role not found: " + roleName));
            roles.add(role);
        }

        user.setRoles(roles);
        User updatedUser = userRepository.save(user);
        return authService.toUserResponse(updatedUser);
    }

    @Transactional
    public UserResponse updateUserStatus(UUID userId, String status) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new ResourceNotFoundException("User not found with ID: " + userId));

        user.setStatus(status.toLowerCase().trim());
        User updatedUser = userRepository.save(user);
        return authService.toUserResponse(updatedUser);
    }

    @Transactional
    public UserResponse assignOrganization(UUID userId, UUID organizationId) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new ResourceNotFoundException("User not found with ID: " + userId));

        Organization org = organizationRepository.findById(organizationId)
                .orElseThrow(() -> new ResourceNotFoundException("Organization not found with ID: " + organizationId));

        user.setOrganization(org);
        User updatedUser = userRepository.save(user);
        return authService.toUserResponse(updatedUser);
    }

    @Transactional
    public void deleteUser(UUID userId) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new ResourceNotFoundException("User not found with ID: " + userId));
        // Soft-delete by setting status to suspended or deleted
        user.setStatus("suspended");
        userRepository.save(user);
    }
}
