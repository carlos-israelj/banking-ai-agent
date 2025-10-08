cat > README_DEPLOYMENT.md << 'EOF'
# 🚀 Deployment en Render

## Prerequisitos

- Cuenta en [Render.com](https://render.com)
- Repositorio de GitHub con el código
- API Key de Gemini

## Pasos para Deploy

### 1. Preparar el repositorio
```bash
# Asegurarse de que NO hay API keys en el código
git rm --cached config/settings.py
git add config/settings.py
git commit -m "security: Remove hardcoded API key"
git push