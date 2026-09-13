package com.tarang.auth.dto;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

public class OrganizationResponse {

    private UUID id;
    private String name;
    private String slug;
    private String orgType;
    private String status;
    private Map<String, Object> settings;
    private Instant createdAt;

    public OrganizationResponse() {}

    public OrganizationResponse(UUID id, String name, String slug, String orgType, String status, Map<String, Object> settings, Instant createdAt) {
        this.id = id;
        this.name = name;
        this.slug = slug;
        this.orgType = orgType;
        this.status = status;
        this.settings = settings;
        this.createdAt = createdAt;
    }

    public UUID getId() { return id; }
    public void setId(UUID id) { this.id = id; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getSlug() { return slug; }
    public void setSlug(String slug) { this.slug = slug; }

    public String getOrgType() { return orgType; }
    public void setOrgType(String orgType) { this.orgType = orgType; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public Map<String, Object> getSettings() { return settings; }
    public void setSettings(Map<String, Object> settings) { this.settings = settings; }

    public Instant getCreatedAt() { return createdAt; }
    public void setCreatedAt(Instant createdAt) { this.createdAt = createdAt; }
}
