# build.ps1 - PowerShell Build & Test Script for Infinite Dungeon C++ Algorithms
param(
    [switch]$Test,
    [switch]$Benchmark,
    [switch]$All,
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

# Ensure g++ is reachable
$gxx = (Get-Command g++ -ErrorAction SilentlyContinue)
if (-not $gxx) {
    if (Test-Path "C:\msys64\ucrt64\bin\g++.exe") {
        $env:Path = "C:\msys64\ucrt64\bin;" + $env:Path
        $gxx = "C:\msys64\ucrt64\bin\g++.exe"
    } else {
        Write-Error "g++ compiler not found! Please ensure MinGW/MSYS2 is installed and on PATH."
        exit 1
    }
}

$CppDir = $PSScriptRoot
$BuildDir = Join-Path $CppDir "build"
$IncludeDir = Join-Path $CppDir "include"
$SrcDir = Join-Path $CppDir "src"
$TestsDir = Join-Path $CppDir "tests"
$BenchDir = Join-Path $CppDir "benchmarks"

if ($Clean) {
    if (Test-Path $BuildDir) {
        Write-Host "Cleaning build directory: $BuildDir..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force $BuildDir
    }
}

if (-not (Test-Path $BuildDir)) {
    New-Item -ItemType Directory -Path $BuildDir | Out-Null
}

$CommonSources = @(
    (Join-Path $SrcDir "traversal.cpp"),
    (Join-Path $SrcDir "pathfinding.cpp"),
    (Join-Path $SrcDir "dungeon_generator.cpp"),
    (Join-Path $SrcDir "knapsack.cpp"),
    (Join-Path $SrcDir "backtracking_puzzle.cpp")
)

$TestExe = Join-Path $BuildDir "test_algorithms.exe"
$BenchExe = Join-Path $BuildDir "benchmark_runner.exe"
$SharedDll = Join-Path $BuildDir "libdungeon_algorithms.dll"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Building Infinite Dungeon C++ Algorithm Suite (C++17, -O3)" -ForegroundColor Cyan
Write-Host " Compiler: $(g++ --version | Select-Object -First 1)" -ForegroundColor DarkGray
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Compile Unit Tests
Write-Host "Compiling test_algorithms.exe..." -ForegroundColor Green
$TestSources = $CommonSources + @((Join-Path $TestsDir "test_algorithms.cpp"))
& g++ -std=c++17 -O3 -Wall -Wextra -I "$IncludeDir" $TestSources -o "$TestExe"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to compile unit tests."
    exit 1
}

# 2. Compile Benchmarks
Write-Host "Compiling benchmark_runner.exe..." -ForegroundColor Green
$BenchSources = $CommonSources + @((Join-Path $BenchDir "benchmark_runner.cpp"))
& g++ -std=c++17 -O3 -Wall -Wextra -I "$IncludeDir" $BenchSources -o "$BenchExe"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to compile benchmarks."
    exit 1
}

# 3. Compile Shared Library (DLL) for optional interop
Write-Host "Compiling libdungeon_algorithms.dll..." -ForegroundColor Green
& g++ -std=c++17 -O3 -shared -I "$IncludeDir" $CommonSources -o "$SharedDll"
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Could not build shared DLL (non-fatal)."
}

Write-Host "`nBuild succeeded! Binaries located in: $BuildDir" -ForegroundColor Green

# Run Tests if requested
if ($Test -or $All -or (-not $Benchmark)) {
    Write-Host "`n>>> Running C++ Unit Tests <<<`n" -ForegroundColor Magenta
    & "$TestExe"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "One or more C++ unit tests failed!"
        exit $LASTEXITCODE
    }
}

# Run Benchmarks if requested
if ($Benchmark -or $All) {
    Write-Host "`n>>> Running C++ Benchmarks <<<`n" -ForegroundColor Magenta
    & "$BenchExe"
}
