# Batch runner — runs all 28 scenarios and saves JSON to test_reports/
param([string]$Scenarios = "")

$runner = "simulation/test_reports/runner.py"
$python = ".\venv\Scripts\python.exe"

$all = @(
    "a1_default","a2_extended","a3_small","a4_large",
    "b1_dictator","b2_utopian","b3_laissez_faire","b4_welfare_state",
    "c1_famine","c2_drought","c3_abundance","c4_high_crime","c5_unstable",
    "d1_all_poor","d2_all_rich","d3_high_morality","d4_low_morality","d5_high_anger",
    "e1_zero_tax","e2_max_welfare","e3_huge_food_cost","e4_sparse","e5_dense",
    "f1_tax_cut","f2_welfare_intro","f3_police",
    "g1_with_ai","g2_no_ai",
    "h1_random"
)

$to_run = if ($Scenarios) { $Scenarios -split "," } else { $all }

$total = $to_run.Count
$i = 0
foreach ($s in $to_run) {
    $i++
    $outfile = "simulation/test_reports/${s}.json"
    Write-Host "[$i/$total] Running $s ..."
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    & $python $runner $s 2>&1 | Out-File -FilePath $outfile -Encoding utf8
    $sw.Stop()
    Write-Host "  done in $([math]::Round($sw.Elapsed.TotalSeconds,1))s -> $outfile"
}

Write-Host "All scenarios complete."
