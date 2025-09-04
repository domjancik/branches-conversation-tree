param(
  [int]$Port = 8742
)

# Simple static file server using .NET HttpListener
Add-Type -AssemblyName System.Net
Add-Type -AssemblyName System.IO.Compression.FileSystem | Out-Null

$listener = New-Object System.Net.HttpListener
$prefix = "http://localhost:$Port/"
$listener.Prefixes.Add($prefix)
$listener.Start()

Write-Host "Serving $(Get-Location) at $prefix"
Write-Host "Press Ctrl+C to stop."

$root = (Get-Location).Path

try {
  while ($listener.IsListening) {
    $context = $listener.GetContext()
    Start-Job -ArgumentList $context,$root -ScriptBlock {
      param($ctx,$rootPath)
      try {
        $req = $ctx.Request
        $res = $ctx.Response
        $path = [System.Uri]::UnescapeDataString($req.Url.AbsolutePath.TrimStart('/'))
        if ([string]::IsNullOrEmpty($path)) { $path = 'index.html' }
        $full = Join-Path $rootPath $path
        if ((Test-Path $full) -and -not (Get-Item $full).PSIsContainer) {
          $ext = [System.IO.Path]::GetExtension($full).ToLowerInvariant()
          switch ($ext) {
            '.html' { $res.ContentType = 'text/html; charset=utf-8' }
            '.js'   { $res.ContentType = 'text/javascript; charset=utf-8' }
            '.css'  { $res.ContentType = 'text/css; charset=utf-8' }
            '.json' { $res.ContentType = 'application/json; charset=utf-8' }
            '.png'  { $res.ContentType = 'image/png' }
            '.jpg'  { $res.ContentType = 'image/jpeg' }
            '.jpeg' { $res.ContentType = 'image/jpeg' }
            '.gif'  { $res.ContentType = 'image/gif' }
            '.svg'  { $res.ContentType = 'image/svg+xml' }
            default { $res.ContentType = 'application/octet-stream' }
          }
          $bytes = [System.IO.File]::ReadAllBytes($full)
          $res.ContentLength64 = $bytes.Length
          $res.OutputStream.Write($bytes, 0, $bytes.Length)
        } else {
          $res.StatusCode = 404
          $buf = [System.Text.Encoding]::UTF8.GetBytes("Not Found: $path")
          $res.OutputStream.Write($buf, 0, $buf.Length)
        }
      } catch {
        $err = $_.Exception.Message
        try {
          $ctx.Response.StatusCode = 500
          $buf = [System.Text.Encoding]::UTF8.GetBytes("Server Error: $err")
          $ctx.Response.OutputStream.Write($buf, 0, $buf.Length)
        } catch {}
      } finally {
        try { $ctx.Response.OutputStream.Close() } catch {}
      }
    } | Out-Null
  }
} finally {
  $listener.Stop()
  $listener.Close()
}

