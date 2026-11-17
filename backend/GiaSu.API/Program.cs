using System.Text;
using System.Text.Json;
using System.Threading.RateLimiting;
using FluentValidation;
using GiaSu.API.Middleware;
using GiaSu.Application.Common;
using GiaSu.Application.DTOs.Auth;
using GiaSu.Application.Interfaces;
using GiaSu.Application.Services;
using GiaSu.Application.Validators.Auth;
using GiaSu.Infrastructure.Persistence;
using GiaSu.Infrastructure.Persistence.Repositories;
using GiaSu.Infrastructure.Services;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.ModelBinding;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;
using Serilog;

Log.Logger = new LoggerConfiguration()
    .MinimumLevel.Information()
    .MinimumLevel.Override("Microsoft.EntityFrameworkCore", Serilog.Events.LogEventLevel.Warning)
    .WriteTo.Console()
    .WriteTo.File("Logs/log-.txt", rollingInterval: RollingInterval.Day, retainedFileCountLimit: 14)
    .CreateLogger();

var builder = WebApplication.CreateBuilder(args);
builder.Host.UseSerilog();

// ---------- Swagger (chỉ bật ở Development) ----------
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(options =>
{
    options.SwaggerDoc("v1", new Microsoft.OpenApi.OpenApiInfo
    {
        Title = "Gia Sư API",
        Version = "v1",
        Description = "API nền tảng tìm việc gia sư và quản lý quá trình dạy"
    });

    options.AddSecurityDefinition("Bearer", new Microsoft.OpenApi.OpenApiSecurityScheme
    {
        Name = "Authorization",
        Type = Microsoft.OpenApi.SecuritySchemeType.Http,
        Scheme = "Bearer",
        BearerFormat = "JWT",
        In = Microsoft.OpenApi.ParameterLocation.Header,
        Description = "Dán token JWT (không cần gõ chữ 'Bearer ')"
    });

    // Phải truyền document vào reference thì Swagger UI mới đính token khi "Try it out"
    options.AddSecurityRequirement(document => new Microsoft.OpenApi.OpenApiSecurityRequirement
    {
        { new Microsoft.OpenApi.OpenApiSecuritySchemeReference("Bearer", document), new List<string>() }
    });
});

builder.Services.AddControllers();

// D04: lỗi model binding (JSON hỏng, sai kiểu) cũng trả khuôn ApiResponse<T>, không trả ProblemDetails
builder.Services.Configure<ApiBehaviorOptions>(options =>
{
    options.InvalidModelStateResponseFactory = context =>
    {
        // Chỉ trả tên trường, không trả ErrorMessage gốc của .NET vì nó lộ tên class nội bộ (NFR-02)
        var bodyParameterNames = context.ActionDescriptor.Parameters
            .Where(p => p.BindingInfo?.BindingSource == BindingSource.Body)
            .Select(p => p.Name)
            .ToHashSet();

        var errors = context.ModelState
            .Where(entry => entry.Value is not null && entry.Value.Errors.Count > 0)
            .Where(entry => !bodyParameterNames.Contains(entry.Key))
            .Select(entry =>
            {
                var field = string.Join('.', entry.Key.TrimStart('$', '.').Split('.')
                    .Select(JsonNamingPolicy.CamelCase.ConvertName));
                return string.IsNullOrEmpty(field)
                    ? "Dữ liệu gửi lên không đọc được (sai định dạng hoặc vượt quá dung lượng cho phép)."
                    : $"Trường '{field}' bị thiếu hoặc sai kiểu dữ liệu.";
            })
            .Distinct()
            .ToList();

        return new BadRequestObjectResult(ApiResponse<object>.Fail(errors));
    };

    // Để UseStatusCodePages bên dưới bọc 404/405/415 thành ApiResponse
    options.SuppressMapClientErrors = true;
});

builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("DefaultConnection"))
        .UseSnakeCaseNamingConvention());

// ---------- Đăng ký DI theo module ----------
// Mỗi module thêm một khối riêng: Repository → Service → Validator.
// Merge bị xung đột ở đây thì GIỮ CẢ HAI PHÍA.

// Hạ tầng dùng chung
builder.Services.AddScoped<IPasswordHasher, PasswordHasherService>();
builder.Services.AddScoped<ITokenService, TokenService>();

// Module Auth (FR-01)
builder.Services.AddScoped<IAuthRepository, AuthRepository>();
builder.Services.AddScoped<IAuthService, AuthService>();
builder.Services.AddScoped<IValidator<LoginRequest>, LoginRequestValidator>();

builder.Services.AddExceptionHandler<GlobalExceptionHandler>();
builder.Services.AddProblemDetails();

// ---------- Xác thực JWT (D06) ----------
var jwtSection = builder.Configuration.GetSection("Jwt");
var jwtKey = jwtSection["Key"]
    ?? throw new InvalidOperationException("Thiếu cấu hình Jwt:Key trong user-secrets.");

builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.MapInboundClaims = false; // giữ nguyên tên claim gốc ("sub", "role")

        // D04: 401/403 mặc định có body rỗng — ghi đè để cũng theo ApiResponse<T>
        options.Events = new JwtBearerEvents
        {
            OnChallenge = async context =>
            {
                context.HandleResponse();
                context.Response.StatusCode = StatusCodes.Status401Unauthorized;
                context.Response.ContentType = "application/json";

                var message = context.AuthenticateFailure is SecurityTokenExpiredException
                    ? "Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại."
                    : "Chưa đăng nhập hoặc token không hợp lệ.";

                await context.Response.WriteAsJsonAsync(ApiResponse<object>.Fail(message));
            },
            OnForbidden = async context =>
            {
                context.Response.StatusCode = StatusCodes.Status403Forbidden;
                context.Response.ContentType = "application/json";
                await context.Response.WriteAsJsonAsync(
                    ApiResponse<object>.Fail("Bạn không có quyền thực hiện hành động này."));
            }
        };

        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidIssuer = jwtSection["Issuer"],
            ValidateAudience = true,
            ValidAudience = jwtSection["Audience"],
            ValidateIssuerSigningKey = true,
            IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(jwtKey)),
            ValidateLifetime = true,
            ClockSkew = TimeSpan.FromMinutes(1),
            ValidAlgorithms = new[] { SecurityAlgorithms.HmacSha256 },
            RoleClaimType = "role",
            NameClaimType = System.IdentityModel.Tokens.Jwt.JwtRegisteredClaimNames.Sub,
        };
    });

builder.Services.AddAuthorization();

// ---------- CORS: chỉ mở cho origin của frontend, không AllowAnyOrigin ----------
const string FrontendCorsPolicy = "FrontendPolicy";
var allowedOrigins = builder.Configuration.GetSection("Cors:AllowedOrigins").Get<string[]>()
    ?? throw new InvalidOperationException("Thiếu cấu hình Cors:AllowedOrigins trong appsettings.");

builder.Services.AddCors(options =>
    options.AddPolicy(FrontendCorsPolicy, policy =>
        policy.WithOrigins(allowedOrigins).AllowAnyHeader().AllowAnyMethod()));

// ---------- D08: rate limit riêng cho /api/auth/login ----------
builder.Services.AddRateLimiter(options =>
{
    options.RejectionStatusCode = StatusCodes.Status429TooManyRequests;

    options.AddPolicy("LoginPolicy", httpContext =>
        RateLimitPartition.GetFixedWindowLimiter(
            partitionKey: httpContext.Connection.RemoteIpAddress?.ToString() ?? "unknown",
            factory: _ => new FixedWindowRateLimiterOptions
            {
                PermitLimit = 5,
                Window = TimeSpan.FromMinutes(1),
                QueueLimit = 0
            }));

    options.OnRejected = async (context, cancellationToken) =>
    {
        context.HttpContext.Response.ContentType = "application/json";
        await context.HttpContext.Response.WriteAsJsonAsync(
            ApiResponse<object>.Fail("Bạn đã thử đăng nhập quá nhiều lần. Vui lòng đợi 1 phút rồi thử lại."),
            cancellationToken);
    };
});

var app = builder.Build();

app.UseMiddleware<SecurityHeadersMiddleware>(); // D09: đứng đầu để mọi response đều mang header
app.UseExceptionHandler();

// D04: bọc các response framework tự sinh mà không có body (404 sai route, 405, 415)
app.UseStatusCodePages(async statusCodeContext =>
{
    var response = statusCodeContext.HttpContext.Response;
    response.ContentType = "application/json";

    var message = response.StatusCode switch
    {
        StatusCodes.Status404NotFound => "Không tìm thấy đường dẫn yêu cầu.",
        StatusCodes.Status405MethodNotAllowed => "Phương thức HTTP không được hỗ trợ cho đường dẫn này.",
        StatusCodes.Status415UnsupportedMediaType => "Định dạng dữ liệu không được hỗ trợ (kiểm tra lại Content-Type).",
        _ => "Yêu cầu không hợp lệ."
    };

    await response.WriteAsJsonAsync(ApiResponse<object>.Fail(message));
});

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI(options => options.SwaggerEndpoint("/swagger/v1/swagger.json", "Gia Sư API v1"));
}

app.UseHttpsRedirection();
app.UseCors(FrontendCorsPolicy);   // trước Authentication để preflight OPTIONS không bị 401
app.UseRateLimiter();              // trước Authentication: chặn sớm
app.UseAuthentication();
app.UseMiddleware<ActiveUserMiddleware>();
app.UseAuthorization();
app.MapControllers();

// Seed tài khoản Admin đầu tiên khi bảng users trống. App KHÔNG tự chạy migration.
using (var scope = app.Services.CreateScope())
{
    var dbContext = scope.ServiceProvider.GetRequiredService<AppDbContext>();
    var passwordHasher = scope.ServiceProvider.GetRequiredService<IPasswordHasher>();
    await DbInitializer.SeedAsync(dbContext, passwordHasher);
}

app.Run();
Log.CloseAndFlush();

// Cho phép project test dùng WebApplicationFactory<Program> sau này
public partial class Program;
