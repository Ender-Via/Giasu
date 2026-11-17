using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Design;

namespace GiaSu.Infrastructure.Persistence;

// Chỉ dùng cho lệnh `dotnet ef migrations add`: tạo migration không cần kết nối DB
// và không cần user-secrets. Lệnh `dotnet ef database update` vẫn chạy qua GiaSu.API
// (--startup-project) để đọc connection string thật từ user-secrets.
public class DesignTimeDbContextFactory : IDesignTimeDbContextFactory<AppDbContext>
{
    public AppDbContext CreateDbContext(string[] args)
    {
        var connectionString = Environment.GetEnvironmentVariable("GIASU_DESIGN_CONNECTION")
            ?? "Host=localhost;Database=giasu_design;Username=postgres;Password=postgres";

        var options = new DbContextOptionsBuilder<AppDbContext>()
            .UseNpgsql(connectionString)
            .UseSnakeCaseNamingConvention()
            .Options;

        return new AppDbContext(options);
    }
}
