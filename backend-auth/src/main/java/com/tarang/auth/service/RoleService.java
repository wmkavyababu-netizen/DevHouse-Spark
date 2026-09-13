package com.tarang.auth.service;

import com.tarang.auth.dto.RoleResponse;
import com.tarang.auth.exception.ResourceNotFoundException;
import com.tarang.auth.model.Role;
import com.tarang.auth.repository.RoleRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
public class RoleService {

    private final RoleRepository roleRepository;

    public RoleService(RoleRepository roleRepository) {
        this.roleRepository = roleRepository;
    }

    @Transactional(readOnly = true)
    public List<RoleResponse> listRoles() {
        return roleRepository.findAll().stream()
                .map(this::toRoleResponse)
                .collect(Collectors.toList());
    }

    @Transactional(readOnly = true)
    public RoleResponse getRoleById(UUID id) {
        Role role = roleRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Role not found with ID: " + id));
        return toRoleResponse(role);
    }

    @Transactional(readOnly = true)
    public RoleResponse getRoleByName(String name) {
        Role role = roleRepository.findByName(name.toLowerCase().trim())
                .orElseThrow(() -> new ResourceNotFoundException("Role not found with name: " + name));
        return toRoleResponse(role);
    }

    @Transactional
    public RoleResponse createRole(String name, String description, Map<String, Object> permissions) {
        String normalizedName = name.toLowerCase().trim();
        if (roleRepository.existsByName(normalizedName)) {
            throw new IllegalArgumentException("Role already exists: " + normalizedName);
        }
        Role role = new Role(normalizedName, description, permissions);
        Role saved = roleRepository.save(role);
        return toRoleResponse(saved);
    }

    @Transactional
    public RoleResponse updatePermissions(UUID id, Map<String, Object> permissions) {
        Role role = roleRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Role not found with ID: " + id));
        role.setPermissions(permissions);
        Role updated = roleRepository.save(role);
        return toRoleResponse(updated);
    }

    public RoleResponse toRoleResponse(Role role) {
        return new RoleResponse(
                role.getId(),
                role.getName(),
                role.getDescription(),
                role.getPermissions(),
                role.getCreatedAt()
        );
    }
}
