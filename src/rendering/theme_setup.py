from pathlib import Path
import shutil

class ThemeSetup:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.theme_dir = output_dir / "themes" / "lecture"
        self.theme_dir.mkdir(parents=True, exist_ok=True)
    
    def create_theme(self):
        source_theme = Path(__file__).parent / "theme" / "index.vue"
        if source_theme.exists():
            target_theme = self.theme_dir / "index.vue"
            shutil.copy2(source_theme, target_theme)
            return target_theme
        
        index_vue = """<template>
  <div class="slidev-theme-wrapper">
    <slot />
  </div>
</template>

<style>
@import '../../styles/design-system.css';

.slidev-theme-wrapper {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
  color: var(--color-neutral-800);
  background: white;
}
</style>
"""
        
        index_vue_path = self.theme_dir / "index.vue"
        with open(index_vue_path, "w", encoding="utf-8") as f:
            f.write(index_vue)
        
        return index_vue_path

