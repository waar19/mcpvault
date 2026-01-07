# 기존 빌드 삭제
Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue

# 빌드
python -m build

# 업로드 (토큰 사용)
uvx twine upload dist/* -u __token__ -p pypi-아까그토큰...