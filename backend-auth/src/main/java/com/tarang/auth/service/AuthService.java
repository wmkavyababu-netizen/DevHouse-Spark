package com.tarang.auth.service;

import com.tarang.auth.dto.*;
import com.tarang.auth.exception.AuthException;
import com.tarang.auth.exception.ResourceNotFoundException;
import com.tarang.auth.model.Organization;
import com.tarang.auth.model.RefreshToken;
import com.tarang.auth.model.Role;
import com.tarang.auth.model.User;
import com.tarang.auth.repository.OrganizationRepository;
import com.tarang.auth.repository.RefreshTokenRepository;
import com.tarang.auth.repository.RoleRepository;
import com.tarang.auth.repository.UserRepository;
import com.tarang.auth.security.JwtTokenProvider;
import com.tarang.auth.security.RsaKeyProvider;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.*;
import java.util.stream.Collectors;

@Service
public class AuthService {

    private final UserRepository userRepository;
    private final RoleRepository roleRepository;
    private final OrganizationRepository organizationRepository;
    private final RefreshTokenRepository refreshTokenRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtTokenProvider jwtTokenProvider;
    private final RsaKeyProvider rsaKeyProvider;

    @Value("${jwt.refresh-expiration-days:30}")
    private long refreshExpirationDays;

    private final SecureRandom secureRandom = new SecureRandom();

    public AuthService(UserRepository userRepository,
                       RoleRepository roleRepository,
                       OrganizationRepository organizationRepository,
                       RefreshTokenRepository refreshTokenRepository,
                       PasswordEncoder passwordEncoder,
                       JwtTokenProvider jwtTokenProvider,
                       RsaKeyProvider rsaKeyProvider) {
        this.userRepository = userRepository;
        this.roleRepository = roleRepository;
        this.organizationRepository = organizationRepository;
        this.refreshTokenRepository = refreshTokenRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtTokenProvider = jwtTokenProvider;
        this.rsaKeyProvider = rsaKeyProvider;
    }

    @Transactional
    public AuthResponse register(RegisterRequest request) {
        if (userRepository.existsByEmailIgnoreCase(request.getEmail())) {
            throw new AuthException("An account with this email already exists: " + request.getEmail());
        }

        // Link or create organization
        Organization org = null;
        if (request.getOrganizationName() != null && !request.getOrganizationName().isBlank()) {
            String slug = generateSlug(request.getOrganizationName());
            org = organizationRepository.findBySlug(slug)
                    .orElseGet(() -> {
                        String type = request.getOrganizationType() != null ? request.getOrganizationType() : "general";
                        return organizationRepository.save(new Organization(request.getOrganizationName(), slug, type));
                    });
        }

        // Hash password with BCrypt
        String passwordHash = passwordEncoder.encode(request.getPassword());
        User user = new User(request.getEmail().toLowerCase().trim(), passwordHash, request.getFullName(), org);

        // Assign default or requested role
        String roleName = request.getRequestedRole() != null && !request.getRequestedRole().isBlank()
                ? request.getRequestedRole().toLowerCase()
                : "survey_operator";

        Role role = roleRepository.findByName(roleName)
                .orElseGet(() -> roleRepository.findByName("survey_operator")
                        .orElseThrow(() -> new IllegalStateException("Default role survey_operator not found in database")));
        user.getRoles().add(role);

        User savedUser = userRepository.save(user);

        // Issue tokens
        String accessToken = jwtTokenProvider.generateAccessToken(savedUser);
        String rawRefreshToken = createAndPersistRefreshToken(savedUser.getId());

        return toAuthResponse(savedUser, accessToken, rawRefreshToken);
    }

    @Transactional
    public AuthResponse login(LoginRequest request) {
        User user = userRepository.findByEmailIgnoreCase(request.getEmail())
                .orElseThrow(() -> new AuthException("Invalid email or password"));

        if (!passwordEncoder.matches(request.getPassword(), user.getPasswordHash())) {
            throw new AuthException("Invalid email or password");
        }

        if (!"active".equalsIgnoreCase(user.getStatus())) {
            throw new AuthException("Account is currently " + user.getStatus() + ". Please contact an administrator.");
        }

        if (user.isTwoFactorEnabled()) {
            if (request.getTwoFactorCode() == null || request.getTwoFactorCode().isBlank()) {
                throw new AuthException("Two-factor authentication code required");
            }
            // Basic 2FA validation hook (e.g. TOTP or demo 6-digit verification)
            if (!isValidTwoFactorCode(user, request.getTwoFactorCode())) {
                throw new AuthException("Invalid two-factor authentication code");
            }
        }

        String accessToken = jwtTokenProvider.generateAccessToken(user);
        String rawRefreshToken = createAndPersistRefreshToken(user.getId());

        return toAuthResponse(user, accessToken, rawRefreshToken);
    }

    @Transactional
    public AuthResponse refreshToken(RefreshTokenRequest request) {
        String tokenHash = sha256Hex(request.getRefreshToken());

        RefreshToken storedToken = refreshTokenRepository.findByTokenHash(tokenHash)
                .orElseThrow(() -> new AuthException("Invalid or revoked refresh token"));

        if (!storedToken.isValid()) {
            throw new AuthException("Refresh token is expired or revoked");
        }

        // Revoke old token as part of rotation
        storedToken.setRevokedAt(Instant.now());
        refreshTokenRepository.save(storedToken);

        User user = userRepository.findById(storedToken.getUserId())
                .orElseThrow(() -> new ResourceNotFoundException("User associated with refresh token not found"));

        if (!"active".equalsIgnoreCase(user.getStatus())) {
            throw new AuthException("Account is deactivated");
        }

        // Generate new access token and new rotated refresh token
        String newAccessToken = jwtTokenProvider.generateAccessToken(user);
        String newRawRefreshToken = createAndPersistRefreshToken(user.getId());

        return toAuthResponse(user, newAccessToken, newRawRefreshToken);
    }

    @Transactional
    public MessageResponse forgotPassword(ForgotPasswordRequest request) {
        Optional<User> userOpt = userRepository.findByEmailIgnoreCase(request.getEmail());
        if (userOpt.isPresent()) {
            User user = userOpt.get();
            // Generate single-use reset token and store in user profile
            String resetToken = UUID.randomUUID().toString();
            Map<String, Object> profile = user.getProfile();
            profile.put("password_reset_token", resetToken);
            profile.put("password_reset_expires_at", Instant.now().plus(24, ChronoUnit.HOURS).toString());
            user.setProfile(profile);
            userRepository.save(user);
            // In a full environment, dispatch email via notification service
        }
        // Always return success message to avoid email enumeration attacks
        return MessageResponse.ok("If an account exists with this email, a password reset link has been issued.");
    }

    @Transactional
    public MessageResponse resetPassword(ResetPasswordRequest request) {
        List<User> users = userRepository.findAll();
        User targetUser = null;

        for (User user : users) {
            Map<String, Object> profile = user.getProfile();
            if (profile != null && request.getToken().equals(profile.get("password_reset_token"))) {
                String expiresAtStr = (String) profile.get("password_reset_expires_at");
                if (expiresAtStr != null && Instant.parse(expiresAtStr).isAfter(Instant.now())) {
                    targetUser = user;
                    break;
                }
            }
        }

        if (targetUser == null) {
            throw new AuthException("Invalid or expired password reset token");
        }

        // Update password and clear reset token
        targetUser.setPasswordHash(passwordEncoder.encode(request.getNewPassword()));
        targetUser.getProfile().remove("password_reset_token");
        targetUser.getProfile().remove("password_reset_expires_at");
        userRepository.save(targetUser);

        // Invalidate all existing refresh tokens for security
        refreshTokenRepository.revokeAllUserTokens(targetUser.getId(), Instant.now());

        return MessageResponse.ok("Password has been reset successfully. Please log in with your new credentials.");
    }

    @Transactional(readOnly = true)
    public UserResponse getCurrentUser(String email) {
        User user = userRepository.findByEmailIgnoreCase(email)
                .orElseThrow(() -> new ResourceNotFoundException("User not found: " + email));
        return toUserResponse(user);
    }

    private String createAndPersistRefreshToken(UUID userId) {
        // Generate secure 32-byte (256-bit) raw random token
        byte[] randomBytes = new byte[32];
        secureRandom.nextBytes(randomBytes);
        String rawToken = Base64.getUrlEncoder().withoutPadding().encodeToString(randomBytes);

        // Hash token before storing in database (never store plaintext)
        String tokenHash = sha256Hex(rawToken);
        Instant expiresAt = Instant.now().plus(refreshExpirationDays, ChronoUnit.DAYS);

        RefreshToken refreshToken = new RefreshToken(userId, tokenHash, rsaKeyProvider.getKeyId(), expiresAt);
        refreshTokenRepository.save(refreshToken);

        return rawToken;
    }

    private String sha256Hex(String input) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(input.getBytes(StandardCharsets.UTF_8));
            StringBuilder hexString = new StringBuilder();
            for (byte b : hash) {
                String hex = Integer.toHexString(0xff & b);
                if (hex.length() == 1) hexString.append('0');
                hexString.append(hex);
            }
            return hexString.toString();
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException("SHA-256 not available", e);
        }
    }

    private boolean isValidTwoFactorCode(User user, String code) {
        // Placeholder check: verify 6-digit numeric string
        return code != null && code.trim().length() == 6;
    }

    private String generateSlug(String name) {
        return name.toLowerCase()
                .replaceAll("[^a-z0-9]+", "-")
                .replaceAll("^-|-$", "");
    }

    private AuthResponse toAuthResponse(User user, String accessToken, String rawRefreshToken) {
        List<String> roleNames = user.getRoles().stream()
                .map(Role::getName)
                .collect(Collectors.toList());

        UUID orgId = user.getOrganization() != null ? user.getOrganization().getId() : null;
        String orgName = user.getOrganization() != null ? user.getOrganization().getName() : null;

        return new AuthResponse(
                accessToken,
                rawRefreshToken,
                jwtTokenProvider.getExpirationSeconds(),
                user.getId(),
                user.getEmail(),
                user.getFullName(),
                orgId,
                orgName,
                roleNames
        );
    }

    public UserResponse toUserResponse(User user) {
        List<String> roleNames = user.getRoles().stream()
                .map(Role::getName)
                .collect(Collectors.toList());

        UUID orgId = user.getOrganization() != null ? user.getOrganization().getId() : null;
        String orgName = user.getOrganization() != null ? user.getOrganization().getName() : null;

        return new UserResponse(
                user.getId(),
                user.getEmail(),
                user.getFullName(),
                user.getStatus(),
                user.isVerified(),
                user.isTwoFactorEnabled(),
                orgId,
                orgName,
                roleNames,
                user.getProfile(),
                user.getCreatedAt(),
                user.getUpdatedAt()
        );
    }
}
