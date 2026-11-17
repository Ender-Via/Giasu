using GiaSu.Application.DTOs.Auth;
using GiaSu.Application.Validators.Auth;

namespace GiaSu.Tests.Auth;

// Mẫu test cho cả nhóm: mỗi quy tắc nghiệp vụ một test, tên test nói rõ điều kiện và kết quả.
// Test viết theo khuôn Cho trước / Khi / Thì giống tiêu chí nghiệm thu trong docs.
public class LoginRequestValidatorTests
{
    private readonly LoginRequestValidator _validator = new();

    [Fact]
    public void Email_va_mat_khau_hop_le_thi_qua_validate()
    {
        var result = _validator.Validate(new LoginRequest("giasu@example.com", "MatKhau@123"));

        Assert.True(result.IsValid);
    }

    [Theory]
    [InlineData("", "MatKhau@123")]
    [InlineData("khong-phai-email", "MatKhau@123")]
    [InlineData("giasu@example.com", "")]
    public void Thieu_hoac_sai_dinh_dang_thi_bi_tu_choi(string email, string password)
    {
        var result = _validator.Validate(new LoginRequest(email, password));

        Assert.False(result.IsValid);
    }

    [Fact]
    public void Email_dai_qua_254_ky_tu_thi_bi_tu_choi()
    {
        var longEmail = new string('a', 250) + "@x.vn";

        var result = _validator.Validate(new LoginRequest(longEmail, "MatKhau@123"));

        Assert.Contains(result.Errors, e => e.ErrorMessage == "Email không được dài quá 254 ký tự.");
    }
}
