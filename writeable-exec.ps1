Function Start-ACLCheck {
  param($Target, $ServiceName)

  if ($Target) {
    $acl = Get-Acl $Target -ErrorAction SilentlyContinue
    if ($acl) {
      # Build identity list (user + groups)
      $idList = @("$env:COMPUTERNAME\$env:USERNAME")
      whoami.exe /groups /fo csv |
        ConvertFrom-Csv |
        ForEach-Object { $idList += $_.'group name' }

      $found = $false
      foreach ($ident in $idList) {
        foreach ($ace in $acl.Access | Where-Object { $_.IdentityReference -like "*$ident*" }) {
          $rights = $ace.FileSystemRights
          if ($rights -match 'FullControl|Modify|Write') {
            Write-Host "[!] $ident has $rights on $Target" -ForegroundColor Red
            $found = $true
          }
        }
      }

      # Recurse up directory if no perms found
      if (-not $found -and $Target.Length -gt 3) {
        Start-ACLCheck -Target (Split-Path $Target) -ServiceName $ServiceName
      }
    } elseif ($Target.Length -gt 3) {
      Start-ACLCheck -Target (Split-Path $Target) -ServiceName $ServiceName
    }
  }
}

# Loop through all executable paths of running processes
Get-Process |
  Select-Object -ExpandProperty Path -Unique |
  Where-Object { $_ -and (Test-Path $_) } |
  ForEach-Object { Start-ACLCheck -Target $_ }
