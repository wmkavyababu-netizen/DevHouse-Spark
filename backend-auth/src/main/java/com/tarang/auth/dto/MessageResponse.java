package com.tarang.auth.dto;

public class MessageResponse {

    private String message;
    private boolean success;

    public MessageResponse() {}

    public MessageResponse(String message, boolean success) {
        this.message = message;
        this.success = success;
    }

    public static MessageResponse ok(String message) {
        return new MessageResponse(message, true);
    }

    public static MessageResponse error(String message) {
        return new MessageResponse(message, false);
    }

    public String getMessage() { return message; }
    public void setMessage(String message) { this.message = message; }

    public boolean isSuccess() { return success; }
    public void setSuccess(boolean success) { this.success = success; }
}
