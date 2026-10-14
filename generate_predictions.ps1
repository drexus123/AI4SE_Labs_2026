$data = 'C:\Users\Matus\AI4SE_Labs_2026\Week_03_Prompting\Assignments\Task_2\data'
$input = Import-Csv -LiteralPath (Join-Path $data 'restaurants_dataset.csv')

function Quote-Sql([string]$value) {
    return "'" + $value.Replace("'", "''") + "'"
}

$geo = Get-Content -LiteralPath (Join-Path $data 'restaurants-db.txt') |
    Where-Object { $_ -like 'GEOGRAPHIC(*' } |
    ForEach-Object {
        if ($_ -match '^GEOGRAPHIC\("([^"]+)", "([^"]+)", "([^"]+)"\)$') {
            [pscustomobject]@{ City = $matches[1]; Region = $matches[3] }
        }
    }
$cities = @($geo.City | Sort-Object Length -Descending)
$regions = @($geo.Region | Sort-Object -Unique | Where-Object { $_ -ne 'unknown' })

function Find-City([string]$text) {
    foreach ($city in $cities) {
        if ($text.ToLower().Contains(' in ' + $city.ToLower())) { return $city }
    }
    return $null
}

function Find-Region([string]$text) {
    foreach ($region in ($regions | Sort-Object Length -Descending)) {
        if ($text.ToLower().Contains($region.ToLower())) { return $region }
    }
    return $null
}

function Find-Food([string]$text) {
    $lower = $text.ToLower()
    $match = [regex]::Match($lower, '(?:for|eat|some) ([a-z][a-z/ -]*?) food')
    if ($match.Success) { return $match.Groups[1].Value.Trim() }
    $match = [regex]::Match($lower, '(?:a|some) ([a-z][a-z/ -]*?) restaurants?')
    if ($match.Success) { return $match.Groups[1].Value.Trim() }
    $match = [regex]::Match($lower, 'best ([a-z][a-z/ -]*?) in ')
    if ($match.Success -and $match.Groups[1].Value -ne 'place') {
        return $match.Groups[1].Value.Trim()
    }
    return $null
}

function Base-Query([string]$where) {
    return "SELECT ID, NAME FROM RESTAURANT WHERE $where"
}

$predictions = foreach ($row in $input) {
    $question = $row.question
    $lower = $question.ToLower()
    $city = Find-City $question
    $region = Find-Region $question
    $food = Find-Food $question
    $ratingMatch = [regex]::Match($lower, 'rating above ([0-9]+(?:\.[0-9]+)?)')
    $rating = if ($ratingMatch.Success) { $ratingMatch.Groups[1].Value } else { $null }
    $sql = $null

    if ($lower -match ' on ' -and $city) {
        $streetMatch = [regex]::Match($lower, ' on (.+?) in ' + [regex]::Escape($city.ToLower()))
        if ($streetMatch.Success) {
            $street = $streetMatch.Groups[1].Value.Trim() -replace '[,?]$', ''
            $conditions = @(
                "LOWER(R.CITY_NAME) = $(Quote-Sql $city)",
                "LOWER(L.STREET_NAME) LIKE '%' || $(Quote-Sql $street) || '%'"
            )
            if ($food) { $conditions += "LOWER(R.FOOD_TYPE) = $(Quote-Sql $food)" }
            if ($rating) { $conditions += "R.RATING > $rating" }
            $sql = 'SELECT R.ID, R.NAME FROM RESTAURANT R JOIN LOCATION L ON L.RESTAURANT_ID = R.ID WHERE ' + ($conditions -join ' AND ')
        }
    }

    if (-not $sql -and $lower -match '^where is ' -and $city -and $lower -notmatch '^where is a |^where is an ') {
        $nameMatch = [regex]::Match($question, '(?i)^where is (.+?) in ' + [regex]::Escape($city))
        if ($nameMatch.Success) {
            $name = $nameMatch.Groups[1].Value.Trim()
            $sql = Base-Query "LOWER(NAME) = $(Quote-Sql $name) AND LOWER(CITY_NAME) = $(Quote-Sql $city)"
        }
    }

    if (-not $sql) {
        $conditions = @()
        if ($food) { $conditions += "LOWER(FOOD_TYPE) = $(Quote-Sql $food)" }
        if ($city) {
            $conditions += "LOWER(CITY_NAME) = $(Quote-Sql $city)"
        } elseif ($region) {
            $conditions += "LOWER(CITY_NAME) IN (SELECT CITY_NAME FROM GEOGRAPHIC WHERE LOWER(REGION) = $(Quote-Sql $region))"
        }
        if ($rating) { $conditions += "RATING > $rating" }
        $sql = if ($conditions.Count -eq 0) {
            'SELECT ID, NAME FROM RESTAURANT'
        } else {
            Base-Query ($conditions -join ' AND ')
        }
        if ($lower -match 'best ') { $sql += ' ORDER BY RATING DESC LIMIT 1' }
    }

    [pscustomobject]@{ question = $question; predicted_sql = $sql }
}

$output = Join-Path $data 'restaurants_dataset_predictions.csv'
$csv = $predictions | ConvertTo-Csv -NoTypeInformation
$csv[0] = 'question,predicted_sql'
$csv | Set-Content -LiteralPath $output -Encoding UTF8
Write-Output "Wrote $($predictions.Count) predictions to $output"
