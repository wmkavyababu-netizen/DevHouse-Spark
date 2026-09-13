package com.tarang.auth.service;

import com.tarang.auth.dto.OrganizationResponse;
import com.tarang.auth.exception.ResourceNotFoundException;
import com.tarang.auth.model.Organization;
import com.tarang.auth.repository.OrganizationRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
public class OrganizationService {

    private final OrganizationRepository organizationRepository;

    public OrganizationService(OrganizationRepository organizationRepository) {
        this.organizationRepository = organizationRepository;
    }

    @Transactional(readOnly = true)
    public List<OrganizationResponse> listOrganizations() {
        return organizationRepository.findAll().stream()
                .map(this::toOrgResponse)
                .collect(Collectors.toList());
    }

    @Transactional(readOnly = true)
    public OrganizationResponse getOrganizationById(UUID id) {
        Organization org = organizationRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Organization not found with ID: " + id));
        return toOrgResponse(org);
    }

    @Transactional
    public OrganizationResponse createOrganization(String name, String orgType, Map<String, Object> settings) {
        String slug = name.toLowerCase()
                .replaceAll("[^a-z0-9]+", "-")
                .replaceAll("^-|-$", "");

        if (organizationRepository.existsBySlug(slug)) {
            throw new IllegalArgumentException("Organization with slug already exists: " + slug);
        }

        Organization org = new Organization(name, slug, orgType != null ? orgType : "general");
        if (settings != null) {
            org.setSettings(settings);
        }
        Organization saved = organizationRepository.save(org);
        return toOrgResponse(saved);
    }

    @Transactional
    public OrganizationResponse updateStatus(UUID id, String status) {
        Organization org = organizationRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Organization not found with ID: " + id));
        org.setStatus(status.toLowerCase().trim());
        Organization updated = organizationRepository.save(org);
        return toOrgResponse(updated);
    }

    @Transactional
    public OrganizationResponse updateSettings(UUID id, Map<String, Object> settings) {
        Organization org = organizationRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Organization not found with ID: " + id));
        org.setSettings(settings);
        Organization updated = organizationRepository.save(org);
        return toOrgResponse(updated);
    }

    public OrganizationResponse toOrgResponse(Organization org) {
        return new OrganizationResponse(
                org.getId(),
                org.getName(),
                org.getSlug(),
                org.getOrgType(),
                org.getStatus(),
                org.getSettings(),
                org.getCreatedAt()
        );
    }
}
