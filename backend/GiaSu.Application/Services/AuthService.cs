using GiaSu.Application.DTOs.Auth;
using GiaSu.Application.Interfaces;
using GiaSu.Domain.Constants;

namespace GiaSu.Application.Services;

// FR-01, UC-01: đăng nhập và phân quyền theo vai trò.
public class AuthService : IAuthService
{
    private readonly IAuthRepository _authRepository;
    private readonly IPasswordHasher _passwordHasher;
    private readonly ITokenService _tokenService;

    public AuthService(
        IAuthRepository authRepository,
        IPasswordHasher passwordHasher,
        ITokenService tokenService)
    {
        _authRepository = authRepository;
        _passwordHasher = passwordHasher;
        _tokenService = tokenService;
    }

    public async Task<LoginResponse?> LoginAsync(LoginRequest request)
    {
        // Email chuẩn hóa lowercase trước khi so sánh
        var normalizedEmail = request.Email.Trim().ToLowerInvariant();

        var user = await _authRepository.FindByLoginIdentifierAsync(normalizedEmail);

        // Sai email, sai mật khẩu hay tài khoản bị khóa đều trả cùng một kết quả,
        // để không lộ email nào đang tồn tại trong hệ thống
        if (user is null
            || !_passwordHasher.Verify(user.CredentialReference, request.Password)
            || !user.IsActive)
        {
            return null;
        }

        var roleClaim = Roles.FromRoleId(user.RoleId);
        var tokenResult = _tokenService.GenerateToken(user.Id, roleClaim, user.TokenVersion);

        return new LoginResponse(
            tokenResult.Token,
            tokenResult.ExpiresAtUtc,
            user.Id,
            user.FullName,
            roleClaim);
    }

    // JWT không chứa thông tin cá nhân nên họ tên phải đọc lại từ DB, không lấy từ claim
    public async Task<CurrentUserResponse?> GetCurrentUserAsync(Guid userId)
    {
        var user = await _authRepository.FindByIdAsync(userId);

        if (user is null)
            return null;

        return new CurrentUserResponse(
            user.Id,
            user.FullName,
            Roles.FromRoleId(user.RoleId));
    }

    // D06: tăng token_version làm mọi token đã phát của người dùng mất hiệu lực ngay từ request kế tiếp
    public Task LogoutAsync(Guid userId)
    {
        return _authRepository.IncrementTokenVersionAsync(userId);
    }
}
