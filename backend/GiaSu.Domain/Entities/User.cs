namespace GiaSu.Domain.Entities;

public class User
{
    public Guid Id { get; set; }
    public short RoleId { get; set; }
    public string FullName { get; set; } = null!;
    public string LoginIdentifier { get; set; } = null!; // email, chuẩn hóa lowercase ở Application
    public string CredentialReference { get; set; } = null!; // password hash — PasswordHasher<T>, không lưu plaintext (NFR-02)
    public bool IsActive { get; set; } = true;
    public int TokenVersion { get; set; } // tăng lên thì mọi token cũ hết hiệu lực — không đưa vào DTO (D06)
    public DateTime CreatedAt { get; set; }

    public Role Role { get; set; } = null!;
}
