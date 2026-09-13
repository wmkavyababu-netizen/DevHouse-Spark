package com.tarang.auth.security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.time.Instant;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

@Component
public class RateLimitingFilter extends OncePerRequestFilter {

    private static final int MAX_REQUESTS_PER_MINUTE = 10;
    private static final long WINDOW_MILLIS = 60_000L;

    private static class RequestCounter {
        long windowStart;
        AtomicInteger count;

        RequestCounter(long windowStart) {
            this.windowStart = windowStart;
            this.count = new AtomicInteger(1);
        }
    }

    private final Map<String, RequestCounter> requestCounts = new ConcurrentHashMap<>();

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {
        String path = request.getRequestURI();

        // Apply rate limit specifically to credential and recovery endpoints
        if (isRateLimitedEndpoint(path, request.getMethod())) {
            String clientIp = getClientIp(request);
            String rateLimitKey = clientIp + ":" + path;

            long now = System.currentTimeMillis();
            RequestCounter counter = requestCounts.compute(rateLimitKey, (key, existing) -> {
                if (existing == null || (now - existing.windowStart) > WINDOW_MILLIS) {
                    return new RequestCounter(now);
                } else {
                    existing.count.incrementAndGet();
                    return existing;
                }
            });

            if (counter != null && counter.count.get() > MAX_REQUESTS_PER_MINUTE) {
                response.setStatus(HttpStatus.TOO_MANY_REQUESTS.value());
                response.setContentType(MediaType.APPLICATION_JSON_VALUE);
                response.getWriter().write(String.format(
                    "{\"timestamp\":\"%s\",\"status\":429,\"error\":\"Too Many Requests\",\"message\":\"Rate limit exceeded for %s. Please try again in 1 minute.\"}",
                    Instant.now().toString(), path
                ));
                return;
            }
        }

        filterChain.doFilter(request, response);
    }

    private boolean isRateLimitedEndpoint(String path, String method) {
        if (!"POST".equalsIgnoreCase(method)) {
            return false;
        }
        return path.endsWith("/api/auth/login") ||
               path.endsWith("/api/auth/register") ||
               path.endsWith("/api/auth/forgot-password");
    }

    private String getClientIp(HttpServletRequest request) {
        String xf = request.getHeader("X-Forwarded-For");
        if (xf != null && !xf.isBlank()) {
            return xf.split(",")[0].trim();
        }
        return request.getRemoteAddr();
    }
}
