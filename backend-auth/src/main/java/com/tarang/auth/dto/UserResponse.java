package com.tarang.auth.dto;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.UUID;

public class UserResponse {

    private UUID id;
    private String email;
    private String fullName;
    private String status;
    private boolean isVerified;
    private boolean twoFactorEnabled;
    private UUID organizationId;
    private String organizationName;
    private List<String> roles;
    private Map<String, Object> profile;
    private Instant createdAt;
    private Instant updatedAt;

    public UserResponse() {}

    public UserResponse(UUID id, String email, String fullName, String status,
                        boolean isVerified, boolean twoFactorEnabled,
                        UUID organizationId, String organizationName,
                        List<String> roles, Map<String, Object> profile,
                        Instant createdAt, Instant updatedAt) {
        this.id = id;
        this.email = email;
        this.fullName = fullName;
        this.status = status;
        this.isVerified = isVerified;
        this.twoFactorEnabled = twoFactorEnabled;
        this.organizationId = organizationId;
        this.organizationName = organizationName;
        this.roles = roles;
        this.profile = profile;
        this.createdAt = createdAt;
        this.updatedAt = updatedAt;
    }

    public UUID getId() { return id; }
    public void setId(UUID id) { this.id = id; }

    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }

    public String getFullName() { return fullName; }
    public void setFullName(String fullName) { this.fullName = fullName; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public boolean isVerified() { return isVerified; }
    public void setVerified(boolean verified) { isVerified = verified; }

    public boolean isTwoFactorEnabled() { return twoFactorEnabled; }
    public void setTwoFactorEnabled(boolean twoFactorEnabled) { this.twoFactorEnabled = twoFactorEnabled; }

    public UUID getOrganizationId() { return organizationId; }
    public void setOrganizationId(UUID organizationId) { this.organizationId = organizationId; }

    public String getOrganizationName() { return organizationName; }
    public void setOrganizationName(String organizationName) { this.organizationName = organizationName; }

    public List<String> getRoles() { return roles; }
    public void setRoles(List<String> roles) { this.roles = roles; }

    public Map<String, Object> getProfile() { return profile; }
    public void setProfile(Map<String, Object> profile) { this.profile = profile; }

    public Instant getCreatedAt() { return createdAt; }
    public void setCreatedAt(Instant createdAt) { this.createdAt = createdAt; }

    public Instant getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(Instant updatedAt) { this.updatedAt = updatedAt; }
}
