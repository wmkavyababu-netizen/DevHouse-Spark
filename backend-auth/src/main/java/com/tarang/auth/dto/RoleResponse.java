package com.tarang.auth.dto;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

public class RoleResponse {

    private UUID id;
    private String name;
    private String description;
    private Map<String, Object> permissions;
    private Instant createdAt;

    public RoleResponse() {}

    public RoleResponse(UUID id, String name, String description, Map<String, Object> permissions, Instant createdAt) {
        this.id = id;
        this.name = name;
        this.description = description;
        this.permissions = permissions;
        this.createdAt = createdAt;
    }

    public UUID getId() { return id; }
    public void setId(UUID id) { this.id = id; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }

    public Map<String, Object> getPermissions() { return permissions; }
    public void setPermissions(Map<String, Object> permissions) { this.permissions = permissions; }

    public Instant getCreatedAt() { return createdAt; }
    public void setCreatedAt(Instant createdAt) { this.createdAt = createdAt; }
}
