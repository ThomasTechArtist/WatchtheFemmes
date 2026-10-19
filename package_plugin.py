"""Build the flat ZIP that TRMNL's Import new accepts."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

if __name__ == '__main__':
    root = Path(__file__).parent
    out = root / 'dist' / 'watch-the-femmes.zip'
    out.parent.mkdir(exist_ok=True)
    with ZipFile(out, 'w', ZIP_DEFLATED) as archive:
        for name in ('settings.yml', 'full.liquid'):
            archive.write(root / 'src' / name, arcname=name)
    print(out)
