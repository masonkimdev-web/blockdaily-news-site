param(
  [string]$PublicRoot = "output"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$baselinePath = Join-Path $repoRoot "tests/fixtures/blockchain-guide-baseline.json"
$baseline = Get-Content -Raw -Encoding utf8 $baselinePath | ConvertFrom-Json
$sourcePath = Join-Path $repoRoot ($baseline.source -replace "/", [IO.Path]::DirectorySeparatorChar)
$source = Get-Content -Raw -Encoding utf8 $sourcePath

$start = $source.IndexOf($baseline.immutable_start)
$end = $source.IndexOf($baseline.immutable_end)
if ($start -lt 0 -or $end -le $start) {
  throw "Immutable guide boundaries were not found."
}

$immutable = $source.Substring($start, $end - $start).Replace("`r`n", "`n")
$sha = [Security.Cryptography.SHA256]::Create()
try {
  $hash = ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($immutable)))).Replace("-", "").ToLowerInvariant()
} finally {
  $sha.Dispose()
}
if ($hash -ne $baseline.sha256) {
  throw "Guide body changed: expected $($baseline.sha256), got $hash"
}

$sectionTitles = @([regex]::Matches($immutable, "(?m)^## (.+?)\r?$") | ForEach-Object { $_.Groups[1].Value })
$stepTitles = @([regex]::Matches($immutable, "(?m)^### (.+?)(?:\s{2})?\r?$") | ForEach-Object { $_.Groups[1].Value.TrimEnd() })
$imageMatches = @([regex]::Matches($immutable, '<img[^>]+src="([^"]+)"[^>]+alt="([^"]*)"'))

if (($sectionTitles -join "`n") -ne (@($baseline.section_titles) -join "`n")) { throw "Guide section titles or order changed." }
if (($stepTitles -join "`n") -ne (@($baseline.step_titles) -join "`n")) { throw "Guide step titles or order changed." }
if ($imageMatches.Count -ne $baseline.image_count) { throw "Guide image count changed." }
for ($i = 0; $i -lt $imageMatches.Count; $i++) {
  if ($imageMatches[$i].Groups[1].Value -ne $baseline.images[$i].src -or $imageMatches[$i].Groups[2].Value -ne $baseline.images[$i].alt) {
    throw "Guide image mapping changed at index $i."
  }
}

$outputPath = Join-Path $repoRoot (Join-Path $PublicRoot "blockchain-guide/index.html")
if (-not (Test-Path $outputPath)) { throw "Built guide not found at $outputPath. Run hugo first." }
$html = Get-Content -Raw -Encoding utf8 $outputPath

$h1Count = [regex]::Matches($html, "<h1(?:\s|>)", "IgnoreCase").Count
if ($h1Count -ne 1) { throw "Expected one H1, found $h1Count." }
if ($html -notmatch '<link\s+rel=(?:"canonical"|canonical)\s+href=(?:"https://blockdailynews\.online/blockchain-guide/"|https://blockdailynews\.online/blockchain-guide/)') { throw "Canonical URL is incorrect." }

$ctaMatches = @([regex]::Matches($html, '<a[^>]+data-binance-cta[^>]+>', "IgnoreCase"))
$expectedLocations = @("hero", "before_guide", "middle", "final", "sticky")
$actualLocations = @()
foreach ($match in $ctaMatches) {
  $tag = $match.Value
  $hrefMatch = [regex]::Match($tag, 'href=(?:"([^"]+)"|([^\s>]+))', "IgnoreCase")
  $locationMatch = [regex]::Match($tag, 'data-cta-location=(?:"([^"]+)"|([^\s>]+))', "IgnoreCase")
  $href = if ($hrefMatch.Groups[1].Success) { $hrefMatch.Groups[1].Value } else { $hrefMatch.Groups[2].Value }
  $location = if ($locationMatch.Groups[1].Success) { $locationMatch.Groups[1].Value } else { $locationMatch.Groups[2].Value }
  if ($href -ne $baseline.referral_url) { throw "CTA '$location' has a different referral URL: $href" }
  if ($tag -notmatch 'target=(?:"_blank"|_blank)' -or $tag -notmatch 'rel="[^"]*noopener[^"]*nofollow[^"]*"') { throw "CTA '$location' has incorrect external-link attributes." }
  $actualLocations += $location
}
$actualLocationList = (($actualLocations | Sort-Object -Unique) -join ",")
$expectedLocationList = (($expectedLocations | Sort-Object) -join ",")
if ($actualLocationList -ne $expectedLocationList) {
  throw "CTA locations are incorrect: $($actualLocations -join ', ')"
}
foreach ($eventName in @("blockchain_guide_view", "binance_cta_impression", "binance_cta_click", "outbound_referral_click", "faq_open")) {
  if ($html -notmatch [regex]::Escape($eventName)) { throw "Missing analytics event: $eventName" }
}
if ([regex]::Matches($html, "binance_cta_click").Count -ne 1 -or [regex]::Matches($html, "outbound_referral_click").Count -ne 1) {
  throw "CTA click event handlers may be duplicated."
}
$lazyGuideImages = [regex]::Matches($html, '<img[^>]+loading=(?:"lazy"|lazy)[^>]+decoding=(?:"async"|async)[^>]*>', "IgnoreCase").Count
if ($lazyGuideImages -ne $baseline.image_count) { throw "Expected lazy/async hints on $($baseline.image_count) guide images, found $lazyGuideImages." }

$faqData = Get-Content -Raw -Encoding utf8 (Join-Path $repoRoot "data/blockchain_guide_faq.json") | ConvertFrom-Json
foreach ($faq in $faqData) {
  $questionCount = [regex]::Matches($html, [regex]::Escape($faq.question)).Count
  $answerCount = [regex]::Matches($html, [regex]::Escape($faq.answer)).Count
  if ($questionCount -lt 2 -or $answerCount -lt 2) {
    throw "Visible FAQ or FAQPage JSON-LD is missing: $($faq.question)"
  }
}
if ($html -notmatch '"@type":"FAQPage"') { throw "FAQPage JSON-LD is missing." }
if ($html -notmatch '"@type":"BreadcrumbList"') { throw "BreadcrumbList JSON-LD is missing." }
if ($html -notmatch 'mobile-sticky-wrap' -or $html -notmatch '@media\s*\(min-width:\s*981px\)') { throw "Mobile sticky CTA styles are missing." }

Write-Output "PASS: guide body hash, $($sectionTitles.Count) sections, $($stepTitles.Count) steps, and $($imageMatches.Count) image mappings are unchanged."
Write-Output "PASS: canonical, single H1, FAQ JSON-LD, CTA URLs/locations, external-link attributes, and analytics event names verified."
