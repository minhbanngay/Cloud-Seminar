param([ValidateRange(1,8)][int]$Slide = 8)
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    New-Item -ItemType Directory -Path 'build','review' -Force | Out-Null
    $texInput = '\def\SlideLimit{' + $Slide + '}\input{main.tex}'
    1..2 | ForEach-Object {
        $ErrorActionPreference = 'Continue'
        $buildOutput = & pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory=build -jobname=cloud-part3 $texInput 2>&1
        $buildExit = $LASTEXITCODE
        $ErrorActionPreference = 'Stop'
        $buildOutput | Set-Content -LiteralPath ('build/pass-' + $_ + '.txt') -Encoding UTF8
        if ($buildExit -ne 0) { $buildOutput | Select-Object -Last 45; throw 'LaTeX compilation failed.' }
    }
    $ErrorActionPreference = 'Continue'
    & pdftoppm -f $Slide -l $Slide -singlefile -scale-to 1800 -png build/cloud-part3.pdf ('review/slide-' + $Slide.ToString('00')) 2>build/render-stderr.txt
    $renderExit = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    if ($renderExit -ne 0) { throw 'PDF rendering failed.' }
    $issues = Select-String -LiteralPath build/cloud-part3.log -Pattern 'Overfull|Underfull|LaTeX Warning|Missing character'
    if ($issues) { $issues | ForEach-Object { $_.Line } }
    Copy-Item -LiteralPath build/cloud-part3.pdf -Destination cloud-part3.pdf -Force
    Write-Output ('Built ' + $Slide + ' slide(s); rendered review/slide-' + $Slide.ToString('00') + '.png')
} finally { Pop-Location }
