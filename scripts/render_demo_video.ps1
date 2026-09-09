param(
    [int]$Port = 8876,
    [switch]$ReuseAudio
)

$ErrorActionPreference = "Stop"
$outputDirectory = Join-Path (Get-Location) "build\video"
New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null

if ($ReuseAudio) {
    .\.venv\Scripts\python.exe scripts\assemble_demo_audio.py `
        --segments docs/demo/video_segments.json `
        --audio-directory build/video/audio `
        --output-directory build/video
}
else {
    & .\scripts\generate_demo_audio.ps1
}

$serverOutput = Join-Path $outputDirectory "demo-server.stdout.log"
$serverError = Join-Path $outputDirectory "demo-server.stderr.log"
$server = Start-Process `
    -FilePath ".\.venv\Scripts\python.exe" `
    -ArgumentList @("-m", "good_neighbor.demo_server", "--host", "127.0.0.1", "--port", $Port) `
    -WorkingDirectory (Get-Location) `
    -RedirectStandardOutput $serverOutput `
    -RedirectStandardError $serverError `
    -WindowStyle Hidden `
    -PassThru

try {
    $ready = $false
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        try {
            Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/state" | Out-Null
            $ready = $true
            break
        }
        catch {
            Start-Sleep -Milliseconds 500
        }
    }
    if (-not $ready) { throw "demo server did not become ready" }

    $env:PLAYWRIGHT_MODULE = "C:\Users\20274\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules\playwright"
    $node = "C:\Users\20274\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe"
    & $node scripts\record_demo_video.cjs "http://127.0.0.1:$Port" "build/video/manifest.json" "build/video"
    if ($LASTEXITCODE -ne 0) { throw "browser recording failed" }
}
finally {
    if (-not $server.HasExited) { Stop-Process -Id $server.Id }
}

$ffmpeg = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Links\ffmpeg.exe"
$video = Join-Path $outputDirectory "good-neighbor-screen.webm"
$audio = Join-Path $outputDirectory "narration.wav"
$final = Join-Path $outputDirectory "good-neighbor-demo.mp4"
& $ffmpeg -y -hide_banner -loglevel warning `
    -i $video -i $audio `
    -vf "subtitles='build/video/captions.srt':force_style='FontName=Segoe UI Semibold,FontSize=13,PrimaryColour=&H00FFFFFF,OutlineColour=&HCC08101D,BorderStyle=3,BackColour=&H9908101D,Outline=1,Shadow=0,MarginV=34,Alignment=2'" `
    -c:v libx264 -preset medium -crf 19 `
    -c:a aac -b:a 192k -movflags +faststart -shortest $final
if ($LASTEXITCODE -ne 0) { throw "final video encoding failed" }

& $ffmpeg -hide_banner -i $final 2>&1 | Select-String "Duration|Video:|Audio:"
Write-Output "VIDEO=$final"
