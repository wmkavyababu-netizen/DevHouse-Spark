package com.tarang.auth.security;

import com.tarang.auth.model.Role;
import com.tarang.auth.model.User;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jws;
import io.jsonwebtoken.Jwts;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Date;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

@Component
public class JwtTokenProvider {

    private final RsaKeyProvider rsaKeyProvider;

    @Value("${jwt.expiration-minutes:60}")
    private long expirationMinutes;

    public JwtTokenProvider(RsaKeyProvider rsaKeyProvider) {
        this.rsaKeyProvider = rsaKeyProvider;
    }

    /**
     * Generate an asymmetric RS256 access token with Key ID in header.
     */
    public String generateAccessToken(User user) {
        Instant now = Instant.now();
        Instant expiry = now.plus(expirationMinutes, ChronoUnit.MINUTES);

        List<String> roleNames = user.getRoles().stream()
                .map(Role::getName)
                .collect(Collectors.toList());

        return Jwts.builder()
                .header()
                .keyId(rsaKeyProvider.getKeyId())
                .and()
                .subject(user.getId().toString())
                .claim("email", user.getEmail())
                .claim("full_name", user.getFullName())
                .claim("organization_id", user.getOrganization() != null ? user.getOrganization().getId().toString() : null)
                .claim("roles", roleNames)
                .issuedAt(Date.from(now))
                .expiration(Date.from(expiry))
                .signWith(rsaKeyProvider.getPrivateKey(), Jwts.SIG.RS256)
                .compact();
    }

    /**
     * Validate the token using the public key and return claims.
     */
    public Claims parseAndValidateToken(String token) {
        Jws<Claims> claimsJws = Jwts.parser()
                .verifyWith(rsaKeyProvider.getPublicKey())
                .build()
                .parseSignedClaims(token);
        return claimsJws.getPayload();
    }

    public UUID extractUserId(String token) {
        return UUID.fromString(parseAndValidateToken(token).getSubject());
    }

    public long getExpirationSeconds() {
        return expirationMinutes * 60;
    }
}
