<#
.SYNOPSIS
    Empacota o backend do TechForge como executavel standalone (Fase 16 par.10).

.DESCRIPTION
    Gera um build PyInstaller --onedir do backend (nao --onefile: onefile
    descompacta pra uma pasta temp a cada start, mais lento e mais sujeito
    a bloqueio de antivirus corporativo). O resultado sobe sem exigir
    Python/pip instalados na maquina do usuario final.

    Escopo desta fase: so o executavel do backend. O instalador Windows
    completo (Inno Setup/MSI) fica fora - ver tasks/phase-16-report.md,
    Known Issues.

.EXAMPLE
    ./scripts/build-backend.ps1
#>
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$backend  = Join-Path $repoRoot "core\backend"
$venvPy   = Join-Path $backend ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPy)) {
    throw "Venv nao encontrado em $venvPy. Crie com 'python -m venv .venv' dentro de core/backend antes de empacotar."
}

Write-Host "Instalando PyInstaller no venv do backend..."
& $venvPy -m pip install --quiet pyinstaller

Push-Location $backend
try {
    Write-Host "Empacotando backend (modo onedir)..."
    # --hidden-import aiosqlite: SQLAlchemy resolve o driver por string a
    # partir da DATABASE_URL (sqlite+aiosqlite://...), nao por import
    # estatico - a analise do PyInstaller nao enxerga essa dependencia
    # sozinha sem essa flag.
    # --add-data alembic/alembic.ini: sao dados (scripts de migration lidos
    # por caminho de arquivo em runtime, app/db/migrations.py), nao codigo
    # Python importado - a analise estatica do PyInstaller nunca os veria.
    & $venvPy -m PyInstaller techforge_server.py --name techforge-backend --onedir --distpath "dist-backend" --workpath "build-backend" --specpath "." --hidden-import aiosqlite --add-data "alembic;alembic" --add-data "alembic.ini;." --noconfirm

    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller falhou (exit code $LASTEXITCODE)."
    }
}
finally {
    Pop-Location
}

$exe = Join-Path $backend "dist-backend\techforge-backend\techforge-backend.exe"
Write-Host "Backend empacotado em $exe"
Write-Host "Modulos (modules/installed/) continuam fora do executavel - carregados em runtime do diretorio de dados do usuario, nao do bundle."
