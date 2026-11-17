namespace GiaSu.Domain.Constants;

// Claim "role" trong JWT dùng hằng số tiếng Anh, không dùng roles.name (tiếng Việt) — D05.
public static class Roles
{
    public const string Admin = "Admin";
    public const string Tutor = "Tutor";   // Sinh viên/Gia sư
    public const string Parent = "Parent"; // Phụ huynh

    // Dùng cho [Authorize(Roles = Roles.All)] ở chức năng mọi vai trò đều có (đăng xuất, xem thông báo).
    // Không dùng [Authorize] trống thay cho hằng số này.
    public const string All = Admin + "," + Tutor + "," + Parent;

    private static readonly Dictionary<short, string> RoleIdToClaim = new()
    {
        [1] = Admin,
        [2] = Tutor,
        [3] = Parent,
    };

    // Phải đứng sau RoleIdToClaim: field tĩnh khởi tạo theo thứ tự trong file
    private static readonly Dictionary<string, short> ClaimToRoleId =
        RoleIdToClaim.ToDictionary(pair => pair.Value, pair => pair.Key);

    public static string FromRoleId(short roleId)
    {
        if (!RoleIdToClaim.TryGetValue(roleId, out var claim))
            throw new ArgumentOutOfRangeException(nameof(roleId), $"role_id không hợp lệ: {roleId}");
        return claim;
    }

    // Phân biệt hoa thường: chỉ nhận đúng 3 hằng số ở trên
    public static bool IsValid(string? role) => role is not null && ClaimToRoleId.ContainsKey(role);

    public static short ToRoleId(string role)
    {
        if (!ClaimToRoleId.TryGetValue(role, out var roleId))
            throw new ArgumentOutOfRangeException(nameof(role), $"Vai trò không hợp lệ: {role}");
        return roleId;
    }
}
