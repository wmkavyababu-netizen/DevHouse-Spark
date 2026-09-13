package com.tarang.auth.controller;

import com.tarang.auth.dto.MessageResponse;
import com.tarang.auth.dto.UserResponse;
import com.tarang.auth.service.UserService;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.Set;
import java.util.UUID;

@RestController
@RequestMapping("/api/users")
public class UserController {

    private final UserService userService;

    public UserController(UserService userService) {
        this.userService = userService;
    }

    @GetMapping
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Page<UserResponse>> listUsers(
            @RequestParam(required = false) String status,
            @RequestParam(required = false) UUID organizationId,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(defaultValue = "createdAt") String sortBy,
            @RequestParam(defaultValue = "desc") String direction
    ) {
        Sort sort = direction.equalsIgnoreCase("asc") ? Sort.by(sortBy).ascending() : Sort.by(sortBy).descending();
        Page<UserResponse> users = userService.listUsers(status, organizationId, PageRequest.of(page, size, sort));
        return ResponseEntity.ok(users);
    }

    @GetMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN') or hasRole('SURVEY_OPERATOR') or hasRole('MARINE_EXPERT') or hasRole('AUTHORITY') or hasRole('NGO') or hasRole('RESEARCHER')")
    public ResponseEntity<UserResponse> getUserById(@PathVariable UUID id) {
        return ResponseEntity.ok(userService.getUserById(id));
    }

    @PutMapping("/{id}/roles")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<UserResponse> updateUserRoles(
            @PathVariable UUID id,
            @RequestBody Map<String, Set<String>> payload
    ) {
        Set<String> roles = payload.get("roles");
        return ResponseEntity.ok(userService.updateUserRoles(id, roles));
    }

    @PutMapping("/{id}/status")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<UserResponse> updateUserStatus(
            @PathVariable UUID id,
            @RequestBody Map<String, String> payload
    ) {
        String status = payload.get("status");
        return ResponseEntity.ok(userService.updateUserStatus(id, status));
    }

    @PutMapping("/{id}/organization")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<UserResponse> assignOrganization(
            @PathVariable UUID id,
            @RequestBody Map<String, UUID> payload
    ) {
        UUID organizationId = payload.get("organizationId");
        return ResponseEntity.ok(userService.assignOrganization(id, organizationId));
    }

    @DeleteMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<MessageResponse> deleteUser(@PathVariable UUID id) {
        userService.deleteUser(id);
        return ResponseEntity.ok(MessageResponse.ok("User suspended successfully"));
    }
}
