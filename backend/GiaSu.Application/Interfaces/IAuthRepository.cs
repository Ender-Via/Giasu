using GiaSu.Domain.Entities;

namespace GiaSu.Application.Interfaces;

public interface IAuthRepository
{
    Task<User?> FindByLoginIdentifierAsync(string normalizedEmail);
    Task<User?> FindByIdAsync(Guid userId);
    Task IncrementTokenVersionAsync(Guid userId);
}