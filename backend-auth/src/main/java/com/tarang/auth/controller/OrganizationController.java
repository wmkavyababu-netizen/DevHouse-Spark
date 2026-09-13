package com.tarang.auth.controller;

import com.tarang.auth.dto.OrganizationResponse;
import com.tarang.auth.service.OrganizationService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/organizations")
public class OrganizationController {

    private final OrganizationService organizationService;

    public OrganizationController(OrganizationService organizationService) {
        this.organizationService = organizationService;
    }

    @GetMapping
    public ResponseEntity<List<OrganizationResponse>> listOrganizations() {
        return ResponseEntity.ok(organizationService.listOrganizations());
    }

    @GetMapping("/{id}")
    public ResponseEntity<OrganizationResponse> getOrganizationById(@PathVariable UUID id) {
        return ResponseEntity.ok(organizationService.getOrganizationById(id));
    }

    @PostMapping
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<OrganizationResponse> createOrganization(@RequestBody Map<String, Object> payload) {
        String name = (String) payload.get("name");
        String orgType = (String) payload.get("orgType");
        @SuppressWarnings("unchecked")
        Map<String, Object> settings = (Map<String, Object>) payload.get("settings");

        OrganizationResponse created = organizationService.createOrganization(name, orgType, settings);
        return ResponseEntity.status(HttpStatus.CREATED).body(created);
    }

    @PutMapping("/{id}/status")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<OrganizationResponse> updateStatus(
            @PathVariable UUID id,
            @RequestBody Map<String, String> payload
    ) {
        String status = payload.get("status");
        return ResponseEntity.ok(organizationService.updateStatus(id, status));
    }

    @PutMapping("/{id}/settings")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<OrganizationResponse> updateSettings(
            @PathVariable UUID id,
            @RequestBody Map<String, Object> settings
    ) {
        return ResponseEntity.ok(organizationService.updateSettings(id, settings));
    }
}
