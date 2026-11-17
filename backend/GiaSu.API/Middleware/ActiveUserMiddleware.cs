using System.Globalization;
using System.IdentityModel.Tokens.Jwt;
using Microsoft.EntityFrameworkCore;
using GiaSu.Application.Common;
using GiaSu.Domain.Constants;
using GiaSu.Infrastructure.Persistence;

namespace GiaSu.API.Middleware;

public class ActiveUserMiddleware
{
    private readonly RequestDelegate _next;

    public ActiveUserMiddleware(RequestDelegate next)
    {
        _next = next;
    }

    // AppDbContext được inject qua tham số InvokeAsync (không phải constructor)
    // vì middleware đăng ký kiểu Singleton, còn DbContext là Scoped — ASP.NET Core
    // tự resolve đúng scope theo từng request khi khai báo kiểu này.
    public async Task InvokeAsync(HttpContext context, AppDbContext dbContext)
    {
        if (context.User.Identity?.IsAuthenticated == true)
        {
            var subClaim = context.User.FindFirst(JwtRegisteredClaimNames.Sub);

            if (subClaim is null || !Guid.TryParse(subClaim.Value, out var userId))
            {
                await WriteUnauthorized(context, "Token không hợp lệ.");
                return;
            }

            // đọc is_active, role_id và token_version trong cùng một truy vấn
            var record = await dbContext.Users
                .Where(u => u.Id == userId)
                .Select(u => new { u.IsActive, u.RoleId, u.TokenVersion })
                .FirstOrDefaultAsync();

            if (record is null || !record.IsActive)
            {
                await WriteUnauthorized(context, "Tài khoản đã bị vô hiệu hóa.");
                return;
            }

            var tokenRoleClaim = context.User.FindFirst("role")?.Value;
            var currentRoleClaim = Roles.FromRoleId(record.RoleId);

            if (tokenRoleClaim != currentRoleClaim)
            {
                await WriteUnauthorized(context, "Vai trò tài khoản đã thay đổi, vui lòng đăng nhập lại.");
                return;
            }

            // D06: token phát trước lần đăng xuất, đặt lại mật khẩu, đổi vai trò hay vô hiệu hóa
            // gần nhất mang tv cũ. Token không có tv (phát trước khi có cơ chế này) cũng bị từ chối.
            var tokenVersionClaim = context.User.FindFirst("tv")?.Value;

            if (!int.TryParse(tokenVersionClaim, NumberStyles.None, CultureInfo.InvariantCulture, out var tokenVersion)
                || tokenVersion != record.TokenVersion)
            {
                await WriteUnauthorized(context, "Phiên đăng nhập đã kết thúc, vui lòng đăng nhập lại.");
                return;
            }
        }

        await _next(context);
    }

    // D04: trả đúng khuôn ApiResponse<T> như mọi endpoint khác, để Frontend chỉ phải
    // xử lý một dạng response.
    private static async Task WriteUnauthorized(HttpContext context, string message)
    {
        context.Response.StatusCode = StatusCodes.Status401Unauthorized;
        context.Response.ContentType = "application/json";
        await context.Response.WriteAsJsonAsync(ApiResponse<object>.Fail(message));
    }
}