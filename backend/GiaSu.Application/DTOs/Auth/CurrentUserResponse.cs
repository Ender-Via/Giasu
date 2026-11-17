namespace GiaSu.Application.DTOs.Auth;

public record CurrentUserResponse(
    Guid UserId,
    string FullName,
    string Role);
