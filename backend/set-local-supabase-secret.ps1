$ErrorActionPreference = "Stop"

$secureValue = Read-Host "Nhập Supabase secret key (ẩn)" -AsSecureString
$secretPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureValue)
try {
    $secretValue = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($secretPointer)
    if ($secretValue -notmatch '^sb_secret_[A-Za-z0-9_-]+$') {
        throw "Key phải là Supabase secret key mới, bắt đầu bằng sb_secret_."
    }

    $envPath = Join-Path $PSScriptRoot ".env"
    $lines = [Collections.Generic.List[string]]::new()
    $lines.AddRange([IO.File]::ReadAllLines($envPath))
    $updated = $false
    for ($index = 0; $index -lt $lines.Count; $index++) {
        if ($lines[$index] -match '^SUPABASE_SECRET_KEY=') {
            $lines[$index] = "SUPABASE_SECRET_KEY=$secretValue"
            $updated = $true
            break
        }
    }
    if (-not $updated) {
        $lines.Add("SUPABASE_SECRET_KEY=$secretValue")
    }
    [IO.File]::WriteAllLines($envPath, $lines, [Text.UTF8Encoding]::new($false))
    Write-Host "Đã lưu SUPABASE_SECRET_KEY vào backend/.env (file Git-ignore)."
}
finally {
    if ($secretPointer -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($secretPointer)
    }
    Remove-Variable secretValue -ErrorAction SilentlyContinue
}
