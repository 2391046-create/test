from pathlib import Path
from PIL import Image

project = Path('/home/ubuntu/student-finance-compass')
icon_paths = [
    project / 'assets/images/icon.png',
    project / 'assets/images/splash-icon.png',
    project / 'assets/images/favicon.png',
    project / 'assets/images/android-icon-foreground.png',
]

for path in icon_paths:
    image = Image.open(path).convert('RGBA')
    # Expo launcher icons render cleanly at 1024px while staying comfortably below checkpoint media limits.
    image = image.resize((1024, 1024), Image.Resampling.LANCZOS)
    image.save(path, format='PNG', optimize=True, compress_level=9)
    print(f'{path}: {path.stat().st_size / 1024:.1f}KB')
