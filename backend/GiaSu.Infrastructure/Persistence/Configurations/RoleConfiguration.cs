using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using GiaSu.Domain.Entities;

namespace GiaSu.Infrastructure.Persistence.Configurations;

public class RoleConfiguration : IEntityTypeConfiguration<Role>
{
    public void Configure(EntityTypeBuilder<Role> builder)
    {
        builder.HasIndex(r => r.Name).IsUnique();

        // Id phải khớp Roles.RoleIdToClaim ở GiaSu.Domain.Constants
        builder.HasData(
            new Role { Id = 1, Name = "Quản trị viên" },
            new Role { Id = 2, Name = "Sinh viên/Gia sư" },
            new Role { Id = 3, Name = "Phụ huynh" }
        );
    }
}
