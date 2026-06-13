# pdw.spec
from PyInstaller.utils.hooks import collect_all, collect_submodules

datas_pdw, binaries_pdw, hidden_pdw = collect_all('pdw')

a = Analysis(
    ['PersonalDataWareHouse.py'],
    pathex=['.'],
    binaries=binaries_pdw,
    datas=[
        ('database', 'database'),
        ('etl', 'etl'),
        ('reports', 'reports'),
        ('utils', 'utils'),
        ('importers', 'importers'),
        *datas_pdw,
    ],
    hiddenimports=[
        *hidden_pdw,
        *collect_submodules('pdw'),
        *collect_submodules('database'),
        *collect_submodules('etl'),
        *collect_submodules('reports'),
        *collect_submodules('utils'),
        *collect_submodules('importers'),
    ],
    excludes=['legacy'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='pdw',
    debug=False,
    strip=False,
    upx=True,
    console=True,
)
