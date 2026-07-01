# platform_post_preview (public 배포 번들)

캐릭터형 소셜앱 **화면 프리뷰** (Streamlit). `characters/<slug>/` 의 `canon.md` + `images/` 를 읽어
홈 피드 · 캐릭터 프로필 · 포스트 상세 구조를 미리봅니다. 상단 드롭다운으로 캐릭터 선택, `◀ ▶` 로 화면 전환.

> ⚠️ **내부 검토/데모용.** 특정 서비스의 UI/로고/CTA 문구를 복제하지 않는 일반화 UI입니다. 가상 성인 캐릭터(fictional, adults only).
> 이 번들은 **메인 private repo와 별개**이며 **요약 `canon.md` + 선별 이미지만** 포함합니다. 상세 스토리·로어북·백로그·Notion 링크 등 IP는 포함하지 않습니다.

## 로컬 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```

→ http://localhost:8501

## Streamlit Community Cloud 배포

1. GitHub에 **새 public repo** 생성 (예: `platform-post-preview`).
2. 이 폴더를 push:
   ```bash
   git init
   git add .
   git commit -m "platform_post_preview public preview"
   git branch -M main
   git remote add origin https://github.com/<YOUR_ID>/platform-post-preview.git
   git push -u origin main
   ```
3. https://share.streamlit.io → **New app** → 위 repo/브랜치 선택 → **Main file path: `app.py`** → Deploy.
4. (선택) **Settings → Secrets** 에 아래를 넣으면 비밀번호 게이트가 켜집니다:
   ```toml
   app_password = "원하는_비밀번호"
   ```
5. (선택) **Settings → Sharing** 에서 뷰어를 특정 이메일로 제한.

## ⚠️ 공개 전 체크리스트

- [ ] `characters/officetel-classmate/images/` 에서 **공개해도 되는 이미지만** 남기기 (노출·정책 위반 소지 이미지는 삭제).
- [ ] `canon.md` 문구가 공개 가능한 수준인지 확인 (이 번들은 이미 요약본).
- [ ] Streamlit Community Cloud **약관(성인/노골적 콘텐츠 금지)** 확인 — 위반 소지가 있으면 공개 배포 대신 자가호스팅(Tailscale/LAN) 권장.
- [ ] 비밀번호 게이트(4번) 또는 뷰어 제한(5번) 중 하나는 설정 권장.

## 캐릭터 추가

`characters/<slug>/` 아래에 `canon.md` + `images/기준선.png`(대표/아바타) + `images/인스타_<제목>.png`(포스트, 파일명 제목 = 캡션) 를 넣으면 드롭다운에 자동으로 뜹니다.
