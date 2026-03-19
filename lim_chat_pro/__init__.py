import os
from pathlib import Path

def get_available_packs():
    """
    [L1 Infrastructure]
    'packs' 폴더 내의 지능 팩(IQ-Pack) 목록을 탐색합니다.
    """
    try:
        # Get path to packs relative to this file
        current_dir = Path(__file__).resolve().parent
        packs_dir = current_dir / "packs"
        
        if not packs_dir.exists():
            return []
            
        return [item.name for item in packs_dir.iterdir() if item.is_dir()]
    except Exception:
        return []

PRO_ROOT = os.path.dirname(os.path.abspath(__file__))
ENGINE_PATH = os.path.join(PRO_ROOT, "engine")
