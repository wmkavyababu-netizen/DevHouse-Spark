package com.tarang.auth.repository;

import com.tarang.auth.model.Organization;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;
import java.util.UUID;

@Repository
public interface OrganizationRepository extends JpaRepository<Organization, UUID> {
    Optional<Organization> findBySlug(String slug);
    Optional<Organization> findByNameIgnoreCase(String name);
    boolean existsBySlug(String slug);
}
