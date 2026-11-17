using FluentValidation;
using GiaSu.Application.DTOs.Auth;

namespace GiaSu.Application.Validators.Auth;

public class LoginRequestValidator : AbstractValidator<LoginRequest>
{
    public LoginRequestValidator()
    {
        // Giới hạn 254 ký tự (độ dài tối đa của địa chỉ email) trước khi kiểm định dạng
        RuleFor(x => x.Email)
            .Cascade(CascadeMode.Stop)
            .NotEmpty().WithMessage("Email không được để trống.")
            .Must(email => email.Trim().Length <= 254)
            .WithMessage("Email không được dài quá 254 ký tự.")
            .EmailAddress().WithMessage("Email không đúng định dạng.");

        RuleFor(x => x.Password)
            .NotEmpty().WithMessage("Mật khẩu không được để trống.");

        // Cố ý KHÔNG kiểm độ dài tối thiểu của mật khẩu ở đây: endpoint này so khớp với hash đã có.
        // Độ mạnh mật khẩu thuộc validator của chức năng đăng ký tài khoản.
    }
}
