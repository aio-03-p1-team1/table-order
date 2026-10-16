"""시작(스플래시) 화면: 룰렛 + 로그인 + 주문 시작.
"""

import os
from html import escape

import streamlit as st

from user import user_repository
from user.state import context as ctx
from user.state.login import poll_login_once
from user.state.roulette import spins_left
from user.state.session import go
from user.ui.common import mini_buttons
from user.ui.login import login_dialog, render_members_log
from user.ui.roulette import render_roulette


def render_splash():
    ss = st.session_state
    poll_login_once()  # 팝업을 닫았거나 다시 그려진 뒤에도 완료된 로그인은 반영
    mini_buttons("splash", home=False)
    store = ctx.STORE  # 매장 정보(이름·지점)는 서버가 Supabase store_info 테이블에서 읽어 준다
    st.html(f'<div class="brand splash-brand"><div class="logo">🍺</div><div><div class="name">{escape(store["name"])}</div>'
            f'<div class="sub">{escape(store["branch"])}</div></div></div>')
    render_roulette()
    member = ss.member
    with st.container(horizontal=True, key="splash_bottom"):
        with st.container(horizontal=True, key="qr_card"):
            if member:
                st.html(f'<div class="qr-text"><div class="a">{escape(member["nickname"])}님</div>'
                        '<div class="b">회원 로그인 완료!</div>'
                        f'<div class="c">남은 룰렛 기회 {spins_left()}회</div></div>')
            else:
                st.html('<div class="qr-text"><div class="a">회원이신가요?</div><div class="b">로그인하고 룰렛 돌리기</div>'
                        '<div class="c">로그인하지 않아도<br>주문은 할 수 있어요.</div></div>')
            if st.button("➕ 다른 회원 로그인" if member else "📱 로그인", key="login_open"):
                login_dialog("more")
            # [개발 전용] DEV_TEST_BUTTON=1 일 때만 보이는 DB 쓰기·읽기 확인 버튼
            if os.getenv("DEV_TEST_BUTTON") == "1" and st.button("🧪 DB 테스트", key="dev_db_test"):
                res = user_repository.dev_db_test()
                if res is None:
                    st.error("서버에 연결할 수 없거나 서버의 DEV_TEST_BUTTON 이 꺼져 있습니다.")
                elif res.get("result") == 1:
                    st.success("1 (정상)")
                else:
                    st.error(f"0 (실패: {res.get('error', '읽은 값이 다름')})")
        with st.container(key="start_cta"):
            st.button("🍴 회원 주문  ›" if member else "🍴 비회원 주문  ›", type="primary", width="stretch",
                      key="start_btn", on_click=go, args=("menu",))
    render_members_log()
