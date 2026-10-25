$ErrorActionPreference = 'Stop'
$reportRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\reports'))
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    foreach ($number in 5..8) {
        $path = Join-Path $reportRoot "Lab_$number.docx"
        $pdf = Join-Path $reportRoot "Lab_$number.pdf"
        $document = $word.Documents.Open($path, $false, $true)
        try {
            $document.Repaginate()
            $document.ExportAsFixedFormat($pdf, 17)
            Write-Output "Lab_$number : $($document.ComputeStatistics(2)) pages"
        } finally { $document.Close(0) }
    }
} finally {
    $word.Quit()
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($word)
}
