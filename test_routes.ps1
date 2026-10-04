$urls = @(
    '/dashboard/reports',
    '/dashboard/settings', 
    '/dashboard/admin',
    '/login',
    '/register'
)

foreach ($p in $urls) {
    $u = 'http://localhost:3000' + $p
    try {
        $r = Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 10
        Write-Host "$u => $($r.StatusCode)"
    } catch {
        Write-Host "$u => FAIL"
    }
}
