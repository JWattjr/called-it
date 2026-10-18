$ErrorActionPreference='Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
$approval=Get-Content -LiteralPath '.secrets/deposit-approval.json' | ConvertFrom-Json
if($approval.approvedTotalWei -ne 20){throw 'Owner approval for the 20-wei demo ceiling is required.'}
$wallets=@(& python -c "import sys;sys.path.insert(0,'scripts');from chain import signer;print(signer(0).address);print(signer(1).address)")
if($LASTEXITCODE -ne 0 -or $wallets.Count -ne 2){throw 'Could not identify generated demo wallets.'}
$amounts=@('14','6')
$path=Join-Path (Get-Location) 'deploy/funding.json'
$journal=if(Test-Path -LiteralPath $path){Get-Content -LiteralPath $path | ConvertFrom-Json -AsHashtable}else{@{approvedTotalWei=20;sourceAccount='moment-grid-studionet';transfers=@{}}}
$previousOptions=$env:NODE_OPTIONS
try {
 $env:NODE_OPTIONS=($previousOptions+' --import=./scripts/explicit-fees.mjs').Trim()
 for($i=0;$i -lt 2;$i++){
  $key=[string]$i
  if($journal.transfers.ContainsKey($key)){continue}
  $log='deploy/funding-'+$key+'.log'
  if(Test-Path -LiteralPath $log){throw 'Existing funding attempt log has no journal entry. Inspect it before retrying to avoid a duplicate transfer.'}
  $ErrorActionPreference='Continue'
  $output=& genlayer.cmd account send $wallets[$i] $amounts[$i] --account moment-grid-studionet --network studionet 2>&1
  $ErrorActionPreference='Stop'
  $output | Set-Content -LiteralPath $log
  $output | Write-Output
  if($LASTEXITCODE -ne 0){throw 'Funding failed; retained the attempt log. Do not repeat blindly.'}
  $hash=[regex]::Matches(($output -join "`n"),'0x[0-9a-fA-F]{64}') | Select-Object -Last 1 -ExpandProperty Value
  if(!$hash){throw 'Funding output lacked a durable transaction hash; inspect the saved log.'}
  $journal.transfers[$key]=@{wallet=$wallets[$i];wei=$amounts[$i];hash=$hash}
  $journal | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $path
 }
} finally {$env:NODE_OPTIONS=$previousOptions}
