$ErrorActionPreference = 'Stop'
$reportRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\reports'))
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$originalPrinter = $word.ActivePrinter
$word.ActivePrinter = 'Microsoft Print to PDF'
try {
    foreach ($number in 5..8) {
        $path = Join-Path $reportRoot "Lab_$number.docx"
        $pdf = Join-Path $reportRoot "Lab_$number.pdf"
        Write-Output "Opening Lab_$number"
        $document = $word.Documents.Open($path, $false, $true)
        try {
            Write-Output "Exporting Lab_$number"
            $document.ExportAsFixedFormat($pdf, 17)
            Write-Output "Exported Lab_$number"
        } finally { $document.Close(0) }
    }
} finally {
    $word.ActivePrinter = $originalPrinter
    $word.Quit()
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($word)
}
