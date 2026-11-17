using Microsoft.EntityFrameworkCore;
using GiaSu.Application.Interfaces;
using GiaSu.Domain.Constants;
using GiaSu.Domain.Entities;

namespace GiaSu.Infrastructure.Persistence;

public static class DbInitializer
{
    // Chỉ dùng để bootstrap tài khoản Admin đầu tiên lúc setup dự án.
    // KHÔNG dùng làm chuẩn bảo mật lâu dài — đổi mật khẩu này ngay sau khi seed.
    private const string SeedAdminEmail = "admin@giasu.local";
    private const string SeedAdminPassword = "Admin@123456";

    public static async Task SeedAsync(AppDbContext dbContext, IPasswordHasher passwordHasher)
    {
        var hasAnyUser = await dbContext.Users.AnyAsync();
        if (hasAnyUser)
            return; // đã seed rồi, hoặc đã có user thật — không seed lại

        var admin = new User
        {
            Id = Guid.NewGuid(),
            RoleId = Roles.ToRoleId(Roles.Admin),
            FullName = "Quản trị hệ thống",
            LoginIdentifier = SeedAdminEmail,
            CredentialReference = passwordHasher.Hash(SeedAdminPassword),
            IsActive = true,
            CreatedAt = DateTime.UtcNow,
        };

        dbContext.Users.Add(admin);
        await dbContext.SaveChangesAsync();
    }
}