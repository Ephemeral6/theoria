$rows = @()
foreach ($p in Get-CimInstance Win32_Process -Filter "Name='python.exe'") {
  $c = [string]$p.CommandLine
  $tag = $null
  if ($c -like '*monitor\reflex.py*' -or $c -like '*monitor/reflex.py*') { $tag = 'reflex' }
  elseif ($c -like '*ci_merge.py*') { $tag = 'ci_merge' }
  elseif ($c -like '*scan.py*') { $tag = 'scan' }
  if ($tag) {
    $age = [int]((Get-Date) - $p.CreationDate).TotalSeconds
    $rows += ("{0}:{1}(ppid{2},{3}s)" -f $tag, $p.ProcessId, $p.ParentProcessId, $age)
  }
}
($rows -join ' ')
