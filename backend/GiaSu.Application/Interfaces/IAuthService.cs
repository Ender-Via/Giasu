using GiaSu.Application.DTOs.Auth;

namespace GiaSu.Application.Interfaces;

public interface IAuthService
{
    Task<LoginResponse?> LoginAsync(LoginRequest request);
    Task<CurrentUserResponse?> GetCurrentUserAsync(Guid userId);
    Task LogoutAsync(Guid userId);
}