# Tai tu lieu cho Log 011 (Cho chong tang Lien Xo, 1941)
# - Anh Wikimedia Commons: CHI lay Public Domain / CC0 / No restrictions (tu dong bo anh co giay phep khac)
# - Canh quay Pexels (Pexels License) qua API
# Cach chay: chuot phai file nay -> Run with PowerShell. Xong se co file log011_assets.zip canh file nay.
$ErrorActionPreference = 'Continue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$UA = 'TheWarLogbookResearch/1.0 (https://www.youtube.com/@TheWarLogbook; educational history documentary)'
$root = if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }
$out = Join-Path $root 'log011_assets'
$imgDir = Join-Path $out 'images'
$vidDir = Join-Path $out 'pexels'
New-Item -ItemType Directory -Force -Path $imgDir, $vidDir | Out-Null
$api = 'https://commons.wikimedia.org/w/api.php'

function Call-Api($params) {
    $q = ($params.GetEnumerator() | ForEach-Object { "$($_.Key)=$([Uri]::EscapeDataString([string]$_.Value))" }) -join '&'
    for ($i = 0; $i -lt 6; $i++) {
        try { return Invoke-RestMethod -Uri "$api`?$q" -UserAgent $UA -TimeoutSec 60 }
        catch { Write-Host "  API loi, cho 20s..." -ForegroundColor Yellow; Start-Sleep 20 }
    }
    return $null
}

# ---------------- 1. ANH WIKIMEDIA COMMONS ----------------
$searches = @(
    @{ q = 'anti-tank dog'; n = 10 },
    @{ q = 'Soviet dog mine World War II'; n = 8 },
    @{ q = 'Red Army dogs 1941'; n = 8 },
    @{ q = 'Soviet military dog handler'; n = 8 },
    @{ q = 'Red Army dog training'; n = 6 },
    @{ q = 'dogs Soviet army Great Patriotic War'; n = 6 },
    @{ q = 'Operation Barbarossa German tanks 1941'; n = 8 },
    @{ q = 'Panzer III Eastern Front 1941'; n = 6 },
    @{ q = 'German tanks Soviet Union 1941'; n = 6 },
    @{ q = 'T-34 1941'; n = 6 },
    @{ q = 'KV-1 tank 1941'; n = 4 },
    @{ q = 'Soviet tank crew 1941'; n = 4 },
    @{ q = 'Red Army trench 1941'; n = 6 },
    @{ q = 'Red Army soldiers trench 1942'; n = 5 },
    @{ q = 'Soviet soldiers 1941 defence'; n = 5 },
    @{ q = 'Eastern Front 1941 battlefield smoke'; n = 5 },
    @{ q = 'Great Patriotic War poster dog'; n = 4 },
    @{ q = 'Moscow Kremlin 1941'; n = 3 }
)

$titles = New-Object System.Collections.ArrayList
foreach ($s in $searches) {
    $r = Call-Api @{ action = 'query'; list = 'search'; srsearch = $s.q; srnamespace = '6'; srlimit = '30'; format = 'json' }
    if ($r) { $r.query.search | Select-Object -First ($s.n * 3) | ForEach-Object { if (-not $titles.Contains($_.title)) { [void]$titles.Add($_.title) } } }
    Start-Sleep 2
}
Write-Host "Tong so anh can kiem tra: $($titles.Count)"

$log = @(); $kept = 0
foreach ($t in $titles) {
    if ($t -notmatch '\.(jpe?g|png|tif?f)$') { continue }
    $r = Call-Api @{ action = 'query'; titles = $t; prop = 'imageinfo'; iiprop = 'url|extmetadata|size'; iiurlwidth = '1920'; format = 'json' }
    Start-Sleep 2
    if (-not $r) { continue }
    $page = $r.query.pages.PSObject.Properties.Value | Select-Object -First 1
    $ii = $page.imageinfo | Select-Object -First 1
    if (-not $ii) { continue }
    $lic = [string]$ii.extmetadata.LicenseShortName.value
    $ok = ($lic -match 'Public domain|^PD|CC0|No restrictions')
    if (-not $ok) { Write-Host "  BO (giay phep: $lic) $t" -ForegroundColor DarkGray; continue }
    $url = if ($ii.thumburl) { $ii.thumburl } else { $ii.url }
    $name = ($t -replace '^File:', '') -replace '[\\/:*?"<>|]', '_'
    $dest = Join-Path $imgDir $name
    $done = $false
    for ($i = 0; $i -lt 6 -and -not $done; $i++) {
        try { Invoke-WebRequest -Uri $url -UserAgent $UA -OutFile $dest -TimeoutSec 120; $done = $true }
        catch { Write-Host "  Tai loi, cho 30s..." -ForegroundColor Yellow; Start-Sleep 30 }
    }
    if ($done) {
        $kept++; Write-Host "  OK [$lic] $name" -ForegroundColor Green
        $desc = [string]$ii.extmetadata.ImageDescription.value
        if ($desc.Length -gt 400) { $desc = $desc.Substring(0, 400) }
        $log += [pscustomobject]@{ file = $name; title = $t; license = $lic; source = $ii.descriptionurl; artist = [string]$ii.extmetadata.Artist.value; date = [string]$ii.extmetadata.DateTimeOriginal.value; description = $desc }
    }
    Start-Sleep 3
}
$log | ConvertTo-Json -Depth 3 | Out-File -Encoding utf8 (Join-Path $imgDir 'giay_phep.json')
Write-Host "`nAnh: $kept file" -ForegroundColor Cyan

# ---------------- 2. CANH QUAY PEXELS ----------------
$key = $env:PEXELS_API_KEY
if (-not $key) { $key = Read-Host 'Dan Pexels API key (Enter de bo qua phan Pexels)' }
if ($key) {
    $vq = @(
        @{ q = 'german shepherd running'; n = 4 },
        @{ q = 'dog running towards camera'; n = 3 },
        @{ q = 'dog running field'; n = 3 },
        @{ q = 'dog sniffing ground'; n = 3 },
        @{ q = 'hungry dog eating'; n = 2 },
        @{ q = 'dog scared'; n = 2 },
        @{ q = 'dog eyes close up'; n = 3 },
        @{ q = 'battlefield smoke'; n = 3 },
        @{ q = 'thick smoke dark'; n = 3 },
        @{ q = 'dust particles dark'; n = 2 },
        @{ q = 'fog field'; n = 2 },
        @{ q = 'fire embers'; n = 2 },
        @{ q = 'sparks dark'; n = 2 },
        @{ q = 'mud tracks'; n = 2 },
        @{ q = 'old film grain'; n = 2 },
        @{ q = 'barbed wire'; n = 2 },
        @{ q = 'rusty metal'; n = 2 },
        @{ q = 'diesel engine'; n = 2 }
    )
    $vlog = @(); $seen = @{}
    foreach ($s in $vq) {
        $u = "https://api.pexels.com/videos/search?query=$([Uri]::EscapeDataString($s.q))&per_page=15&size=medium"
        try { $r = Invoke-RestMethod -Uri $u -Headers @{ Authorization = $key } -TimeoutSec 60 } catch { Write-Host "  Pexels loi: $($s.q)" -ForegroundColor Yellow; continue }
        $cnt = 0
        foreach ($v in $r.videos) {
            if ($cnt -ge $s.n) { break }
            if ($seen.ContainsKey($v.id)) { continue }
            if ($v.duration -gt 40) { continue }
            # chon ban HD, canh dai toi da 1920
            $f = $v.video_files | Where-Object { $_.file_type -eq 'video/mp4' -and [Math]::Max($_.width, $_.height) -le 1920 -and [Math]::Max($_.width, $_.height) -ge 1080 } | Sort-Object { [Math]::Max($_.width, $_.height) } -Descending | Select-Object -First 1
            if (-not $f) { continue }
            $slug = ($s.q -replace '[^a-z0-9]+', '_')
            $name = "$slug`_$($v.id).mp4"
            try {
                Invoke-WebRequest -Uri $f.link -OutFile (Join-Path $vidDir $name) -TimeoutSec 300
                $seen[$v.id] = 1; $cnt++
                Write-Host "  OK $name ($($f.width)x$($f.height))" -ForegroundColor Green
                $vlog += [pscustomobject]@{ file = $name; url = $v.url; author = $v.user.name; license = 'Pexels License'; query = $s.q }
            } catch { Write-Host "  Tai loi $name" -ForegroundColor Yellow }
            Start-Sleep 1
        }
    }
    $vlog | ConvertTo-Json -Depth 3 | Out-File -Encoding utf8 (Join-Path $vidDir 'pexels_nguon.json')
}

# ---------------- 3. NEN ZIP (tu chia file neu > 95 MB) ----------------
$zip = Join-Path $root 'log011_assets.zip'
if (Test-Path $zip) { Remove-Item $zip }
Compress-Archive -Path "$out\*" -DestinationPath $zip -CompressionLevel Optimal
$size = (Get-Item $zip).Length
Write-Host ("`nXONG: {0} ({1:N0} MB)" -f $zip, ($size / 1MB)) -ForegroundColor Cyan
if ($size -gt 95MB) {
    $buf = New-Object byte[] (95MB); $fs = [IO.File]::OpenRead($zip); $i = 1
    while (($n = $fs.Read($buf, 0, $buf.Length)) -gt 0) {
        $part = "$zip.part$i"; [IO.File]::WriteAllBytes($part, $buf[0..($n - 1)]); Write-Host "  -> $part"; $i++
    }
    $fs.Close()
    Write-Host 'File lon: gui cac file .part1, .part2... cho Claude.' -ForegroundColor Cyan
} else {
    Write-Host 'Gui file log011_assets.zip cho Claude.' -ForegroundColor Cyan
}
Read-Host 'Nhan Enter de dong'
