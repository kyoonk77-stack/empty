#---streamlit run community.py


# -*- coding: utf-8 -*-
import streamlit as st
import sqlite3
import hashlib

# --- 1. 데이터베이스 초기화 (모든 기능 테이블 생성) ---
def init_db():
    conn = sqlite3.connect('entry_data.db')
    c = conn.cursor()
    # 유저: 아이디(PK), 비번, 닉네임, 관리자여부, 차단여부
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, nickname TEXT, is_admin INTEGER, is_banned INTEGER)''')
    # 체크리스트: 아이디, 내용, 완료여부
    c.execute('''CREATE TABLE IF NOT EXISTS memos 
                 (username TEXT, content TEXT, is_done INTEGER)''')
    # 게시판: 글번호, 작성자ID, 닉네임, 제목, 내용, 좋아요, 신고
    c.execute('''CREATE TABLE IF NOT EXISTS posts 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, author_id TEXT, nickname TEXT, title TEXT, content TEXT, likes INTEGER, reports INTEGER)''')
    # 댓글: 글번호, 게시글번호, 작성자ID, 닉네임, 내용
    c.execute('''CREATE TABLE IF NOT EXISTS comments 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, post_id INTEGER, author_id TEXT, nickname TEXT, content TEXT)''')
    
    # [설정된 어드민 계정] ID: tlswldks131129, PW: j131129
    admin_id = "tlswldks131129"
    admin_pw = hashlib.md5("j131129".encode()).hexdigest()
    c.execute("INSERT OR REPLACE INTO users VALUES (?, ?, '총괄관리자', 1, 0)", (admin_id, admin_pw))
    
    conn.commit()
    conn.close()

init_db()

# --- 2. 보안 유틸리티 ---
def make_hashes(password):
    return hashlib.md5(str.encode(password)).hexdigest()

# --- 3. 로그인 세션 관리 ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'username': "", 'nickname': "", 'is_admin': 0})

# --- 4. 사이드바 (로그인/회원가입) ---
st.sidebar.title("🚀 엔트리 메이커")
if not st.session_state['logged_in']:
    auth = st.sidebar.radio("접속 메뉴", ["로그인", "회원가입"])
    u_id = st.sidebar.text_input("아이디")
    u_pw = st.sidebar.text_input("비밀번호", type="password")
    
    if auth == "로그인" and st.sidebar.button("들어가기"):
        conn = sqlite3.connect('entry_data.db'); c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username=? AND password=?', (u_id, make_hashes(u_pw)))
        u = c.fetchone()
        if u:
            if u[4] == 1: st.sidebar.error("🚫 차단된 계정입니다.")
            else:
                st.session_state.update({'logged_in': True, 'username': u_id, 'nickname': u[2], 'is_admin': u[3]})
                st.rerun()
        else: st.sidebar.error("정보가 일치하지 않습니다.")
        conn.close()
    elif auth == "회원가입":
        u_nick = st.sidebar.text_input("닉네임 설정")
        if st.sidebar.button("가입하기"):
            conn = sqlite3.connect('entry_data.db'); c = conn.cursor()
            try:
                c.execute('INSERT INTO users VALUES (?,?,?,0,0)', (u_id, make_hashes(u_pw), u_nick))
                conn.commit(); st.sidebar.success("가입 성공! 로그인해 주세요.")
            except: st.sidebar.error("이미 사용 중인 아이디입니다.")
            conn.close()
else:
    st.sidebar.write(f"🎮 **{st.session_state['nickname']}**님")
    if st.sidebar.button("로그아웃"):
        st.session_state.update({'logged_in': False, 'username': "", 'nickname': "", 'is_admin': 0})
        st.rerun()

# --- 5. 메인 콘텐츠 기능 ---
if st.session_state['logged_in']:
    menu = ["🏠 홈", "💬 커뮤니티", "📝 체크리스트", "⚙️ 설정"]
    if st.session_state['is_admin']: menu.append("🚨 관리자 센터")
    choice = st.sidebar.radio("메뉴 이동", menu)

    # [🏠 홈]
    if choice == "🏠 홈":
        st.title("🏠 홈 대시보드")
        st.subheader(f"안녕하세요, {st.session_state['nickname']}님!")
        c1, c2 = st.columns(2)
        with c1:
            st.info("🔥 **커뮤니티 인기글**")
            conn = sqlite3.connect('entry_data.db'); c = conn.cursor()
            c.execute('SELECT title, likes FROM posts ORDER BY likes DESC LIMIT 3')
            for t, l in c.fetchall(): st.write(f"👍 {l} | {t}")
        with c2:
            st.success("✅ **나의 개발 할 일**")
            c.execute('SELECT content FROM memos WHERE username=? AND is_done=0 LIMIT 3', (st.session_state['username'],))
            for m in c.fetchall(): st.write(f"▫️ {m[0]}")
        conn.close()

    # [💬 커뮤니티 & 검색 & 댓글]
    elif choice == "💬 커뮤니티":
        st.title("💬 커뮤니티")
        search = st.text_input("🔍 제목, 내용, 닉네임으로 검색", placeholder="검색어를 입력하세요...")
        
        with st.expander("📝 새 게시글 작성"):
            t = st.text_input("제목")
            cv = st.text_area("내용")
            if st.button("게시"):
                conn = sqlite3.connect('entry_data.db'); c = conn.cursor()
                c.execute('INSERT INTO posts (author_id, nickname, title, content, likes, reports) VALUES (?,?,?,?,0,0)', 
                          (st.session_state['username'], st.session_state['nickname'], t, cv))
                conn.commit(); conn.close(); st.rerun()

        st.divider()
        conn = sqlite3.connect('entry_data.db'); c = conn.cursor()
        if search:
            sq = f"%{search}%"
            c.execute('SELECT * FROM posts WHERE title LIKE ? OR content LIKE ? OR nickname LIKE ? ORDER BY id DESC', (sq, sq, sq))
        else:
            c.execute('SELECT * FROM posts ORDER BY id DESC')
        
        for p in c.fetchall():
            with st.container(border=True):
                st.subheader(p[3])
                st.caption(f"작성자: {p[2]} | 👍 {p[5]} | 🚨 {p[6]}")
                st.write(p[4])
                col1, col2, _ = st.columns([1, 1, 4])
                if col1.button(f"👍", key=f"l_{p[0]}"):
                    c.execute('UPDATE posts SET likes=likes+1 WHERE id=?', (p[0],)); conn.commit(); st.rerun()
                if col2.button(f"🚨", key=f"r_{p[0]}"):
                    c.execute('UPDATE posts SET reports=reports+1 WHERE id=?', (p[0],)); conn.commit(); st.toast("신고 접수"); st.rerun()
                
                # 댓글 리스트
                c.execute('SELECT nickname, content FROM comments WHERE post_id=?', (p[0],))
                for cn, cc in c.fetchall(): st.write(f"🗨️ **{cn}**: {cc}")
                
                with st.form(key=f"cf_{p[0]}", clear_on_submit=True):
                    ci = st.text_input("댓글 쓰기")
                    if st.form_submit_button("등록"):
                        c.execute('INSERT INTO comments (post_id, author_id, nickname, content) VALUES (?,?,?,?)',
                                  (p[0], st.session_state['username'], st.session_state['nickname'], ci))
                        conn.commit(); st.rerun()
        conn.close()

    # [📝 체크리스트]
    elif choice == "📝 체크리스트":
        st.title("📝 내 개발 체크리스트")
        nt = st.text_input("작업 추가")
        if st.button("추가"):
            conn = sqlite3.connect('entry_data.db'); c = conn.cursor()
            c.execute('INSERT INTO memos VALUES (?,?,0)', (st.session_state['username'], nt))
            conn.commit(); conn.close(); st.rerun()
        conn = sqlite3.connect('entry_data.db'); c = conn.cursor()
        c.execute('SELECT rowid, content, is_done FROM memos WHERE username=?', (st.session_state['username'],))
        for rid, con, don in c.fetchall():
            cl1, cl2 = st.columns([0.8, 0.2])
            chk = cl1.checkbox(con, value=bool(don), key=f"ck_{rid}")
            if chk != don:
                c.execute('UPDATE memos SET is_done=? WHERE rowid=?', (int(chk), rid)); conn.commit()
            if cl2.button("🗑️", key=f"md_{rid}"):
                c.execute('DELETE FROM memos WHERE rowid=?', (rid,)); conn.commit(); st.rerun()
        conn.close()

    # [⚙️ 설정 - 닉네임 변경 및 영구 저장]
    elif choice == "⚙️ 설정":
        st.title("⚙️ 계정 설정")
        st.write(f"현재 닉네임: **{st.session_state['nickname']}**")
        new_nick = st.text_input("새 닉네임 입력")
        if st.button("변경 내용 저장"):
            if new_nick:
                conn = sqlite3.connect('entry_data.db'); c = conn.cursor()
                # 1. 유저 정보 수정
                c.execute('UPDATE users SET nickname=? WHERE username=?', (new_nick, st.session_state['username']))
                # 2. 과거 게시글 닉네임 수정
                c.execute('UPDATE posts SET nickname=? WHERE author_id=?', (new_nick, st.session_state['username']))
                # 3. 과거 댓글 닉네임 수정
                c.execute('UPDATE comments SET nickname=? WHERE author_id=?', (new_nick, st.session_state['username']))
                conn.commit(); conn.close()
                st.session_state['nickname'] = new_nick # 세션 갱신
                st.success("닉네임이 영구적으로 변경되었습니다!"); st.rerun()

    # [🚨 관리자 센터]
    elif choice == "🚨 관리자 센터":
        st.title("🛡️ 관리자 제어판")
        conn = sqlite3.connect('entry_data.db'); c = conn.cursor()
        c.execute('SELECT * FROM posts WHERE reports > 0 ORDER BY reports DESC')
        for rp in c.fetchall():
            with st.container(border=True):
                st.warning(f"🚨 신고 {rp[6]}건 | 작성자: {rp[2]}({rp[1]})")
                st.subheader(rp[3]); st.write(rp[4])
                a1, a2, a3 = st.columns(3)
                if a1.button("✅ 신고 무시", key=f"ig_{rp[0]}", use_container_width=True):
                    c.execute('UPDATE posts SET reports=0 WHERE id=?', (rp[0],)); conn.commit(); st.rerun()
                if a2.button("🗑️ 글 삭제", key=f"pd_{rp[0]}", use_container_width=True):
                    c.execute('DELETE FROM posts WHERE id=?', (rp[0],)); conn.commit(); st.rerun()
                if a3.button("🚫 작성자 차단", key=f"ub_{rp[1]}", use_container_width=True):
                    c.execute('UPDATE users SET is_banned=1 WHERE username=?', (rp[1],))
                    c.execute('DELETE FROM posts WHERE author_id=?', (rp[1],))
                    conn.commit(); st.rerun()
        conn.close()
else:
    st.title("🚀 엔트리 메이커")
    st.info("로그인 후 이용 가능합니다.")
