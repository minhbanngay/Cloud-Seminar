$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    $buildDirectory = Join-Path ([System.IO.Path]::GetTempPath()) ('cloud-seminar-build-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $buildDirectory | Out-Null
    foreach ($pass in 1..2) {
        $ErrorActionPreference = 'Continue'
        $buildOutput = & pdflatex -interaction=nonstopmode -halt-on-error -file-line-error ('-output-directory=' + $buildDirectory) main.tex 2>&1
        $buildExit = $LASTEXITCODE
        $ErrorActionPreference = 'Stop'
        $buildOutput | Set-Content -LiteralPath (Join-Path $buildDirectory ('pass-' + $pass + '.txt')) -Encoding UTF8
        if ($buildExit -ne 0) {
            $buildOutput | Select-Object -Last 40
            throw ('LaTeX compilation failed. Logs: ' + $buildDirectory)
        }
    }
    Copy-Item -LiteralPath (Join-Path $buildDirectory 'main.pdf') -Destination (Join-Path $PSScriptRoot 'main.pdf') -Force
    Write-Output ('Built ' + (Join-Path $PSScriptRoot 'main.pdf') + ' (34 slides).')
    $tempRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath()).TrimEnd('\') + '\'
    $resolvedBuild = (Resolve-Path -LiteralPath $buildDirectory).Path
    if (-not $resolvedBuild.StartsWith($tempRoot, [System.StringComparison]::OrdinalIgnoreCase) -or [System.IO.Path]::GetFileName($resolvedBuild) -notmatch '^cloud-seminar-build-[0-9a-f]{32}$') {
        throw 'Refusing to remove a build directory outside the expected temporary location.'
    }
    Remove-Item -LiteralPath $resolvedBuild -Recurse -Force
} finally {
    Pop-Location
}
