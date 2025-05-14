from pathlib import Path


def load_styles(style: Path) -> str:
    """Opens a style of type qss"""
    try:
        if Path(style).suffix != ".qss":
            raise ValueError(f"The file extension {Path(style).suffix} isn't valid qss")
        
        with open(Path(style).resolve(), 'r') as style_file:
            styles = style_file.read()
            return styles
    except Exception as e:
        print(f"Encountered the following errors \n{e}")