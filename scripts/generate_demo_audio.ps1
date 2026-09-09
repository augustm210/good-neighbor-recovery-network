param(
    [string]$SegmentsPath = "docs/demo/video_segments.json",
    [string]$OutputDirectory = "build/video",
    [string]$VoiceId = "Danielle",
    [string]$Engine = "generative",
    [string]$Region = "ap-southeast-2",
    [string]$Profile = "agents-for-humans-dev"
)

$ErrorActionPreference = "Stop"
$segments = Get-Content -Raw -LiteralPath $SegmentsPath | ConvertFrom-Json
$audioDirectory = Join-Path $OutputDirectory "audio"
New-Item -ItemType Directory -Force -Path $audioDirectory | Out-Null
$ffmpeg = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Links\ffmpeg.exe"
if (-not (Test-Path -LiteralPath $ffmpeg)) {
    throw "ffmpeg is required at $ffmpeg"
}

for ($index = 0; $index -lt $segments.Count; $index++) {
    $prefix = Join-Path $audioDirectory ("segment-{0:D2}" -f ($index + 1))
    $textPath = "$prefix.txt"
    $mp3Path = "$prefix.mp3"
    $wavPath = "$prefix.wav"
    Set-Content -LiteralPath $textPath -Value ([string]$segments[$index].text) -Encoding utf8NoBOM
    aws polly synthesize-speech `
        --engine $Engine `
        --voice-id $VoiceId `
        --language-code en-US `
        --output-format mp3 `
        --sample-rate 24000 `
        --text "file://$textPath" `
        --region $Region `
        --profile $Profile `
        $mp3Path | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Polly synthesis failed for segment $($index + 1)" }
    & $ffmpeg -y -hide_banner -loglevel error -i $mp3Path -ar 24000 -ac 1 $wavPath
    if ($LASTEXITCODE -ne 0) { throw "audio conversion failed for segment $($index + 1)" }
}

.\.venv\Scripts\python.exe scripts\assemble_demo_audio.py `
    --segments $SegmentsPath `
    --audio-directory $audioDirectory `
    --output-directory $OutputDirectory
