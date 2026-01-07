uv pip install build twine --system

# 기존 빌드 폴더 삭제 (깨끗하게 시작)
if (Test-Path dist) { Remove-Item -Recurse -Force dist }

# 빌드 실행 (python 모듈 실행 방식)
python -m build

# 1. 의존성 라이브러리 강제 업데이트
# uv pip install -U packaging twine keyring pkginfo --system

# 2. 다시 업로드 시도
# python -m twine upload dist/*

uvx twine upload dist/*