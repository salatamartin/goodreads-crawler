function ConvertFrom-Base64 {
    param(
        [Parameter(ValueFromPipeline=$true)]
        $Data
    )
    return [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($Data))
}

$username, $password = (Get-Content -Raw .credentials | ConvertFrom-Base64).Split(':') | ForEach-Object { $_.Trim() }

mkdir results -ErrorAction SilentlyContinue
$resultsPath = "$PSScriptRoot\results".Replace('\', '/')

docker run --rm `
    -e GR_USERNAME=$username `
    -e GR_PASSWORD=$password `
    -v "$($resultsPath):/workdir/results" `
    --name crawler `
    crawler