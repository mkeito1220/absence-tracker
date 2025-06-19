import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, date
import calendar

# ページ設定
st.set_page_config(
    page_title="欠席回数管理アプリ",
    page_icon="📚",
    layout="wide"
)

# データファイルのパス
SUBJECTS_FILE = "subjects.json"
ABSENCES_FILE = "absences.json"

def load_subjects():
    """科目データを読み込む"""
    if os.path.exists(SUBJECTS_FILE):
        with open(SUBJECTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_subjects(subjects):
    """科目データを保存する"""
    with open(SUBJECTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(subjects, f, ensure_ascii=False, indent=2)

def load_absences():
    """欠席データを読み込む"""
    if os.path.exists(ABSENCES_FILE):
        with open(ABSENCES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_absences(absences):
    """欠席データを保存する"""
    with open(ABSENCES_FILE, 'w', encoding='utf-8') as f:
        json.dump(absences, f, ensure_ascii=False, indent=2)

def main():
    st.title("📚 欠席回数管理アプリ")
    
    # サイドバーでページ選択
    page = st.sidebar.selectbox(
        "ページを選択",
        ["科目管理", "欠席記録", "欠席状況確認", "時間割表示"]
    )
    
    if page == "科目管理":
        subject_management()
    elif page == "欠席記録":
        absence_recording()
    elif page == "欠席状況確認":
        absence_status()
    elif page == "時間割表示":
        timetable_view()

def subject_management():
    """科目管理ページ"""
    st.header("📖 科目管理")
    
    subjects = load_subjects()
    
    # 新しい科目の追加
    st.subheader("新しい科目を追加")
    col1, col2 = st.columns(2)
    
    with col1:
        new_subject = st.text_input("科目名")
    with col2:
        max_absences = st.number_input("欠席上限回数", min_value=1, value=5)
    
    if st.button("科目を追加"):
        if new_subject and new_subject not in subjects:
            subjects[new_subject] = {"max_absences": max_absences}
            save_subjects(subjects)
            st.success(f"科目「{new_subject}」を追加しました！")
            st.rerun()
        elif new_subject in subjects:
            st.error("この科目は既に登録されています。")
        else:
            st.error("科目名を入力してください。")
    
    # 既存科目の表示と編集
    if subjects:
        st.subheader("登録済み科目")
        for subject, info in subjects.items():
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(f"**{subject}**")
            with col2:
                st.write(f"上限: {info['max_absences']}回")
            with col3:
                if st.button("削除", key=f"del_{subject}"):
                    del subjects[subject]
                    save_subjects(subjects)
                    # 対応する欠席データも削除
                    absences = load_absences()
                    if subject in absences:
                        del absences[subject]
                        save_absences(absences)
                    st.success(f"科目「{subject}」を削除しました！")
                    st.rerun()

def absence_recording():
    """欠席記録ページ"""
    st.header("📝 欠席記録")
    
    subjects = load_subjects()
    absences = load_absences()
    
    if not subjects:
        st.warning("まず科目を登録してください。")
        return
    
    # 欠席記録フォーム
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_subject = st.selectbox("科目を選択", list(subjects.keys()))
    
    with col2:
        absence_date = st.date_input("欠席日", value=date.today())
    
    with col3:
        absence_reason = st.text_input("欠席理由（任意）")
    
    if st.button("欠席を記録"):
        if selected_subject not in absences:
            absences[selected_subject] = []
        
        absence_record = {
            "date": absence_date.isoformat(),
            "reason": absence_reason
        }
        
        absences[selected_subject].append(absence_record)
        save_absences(absences)
        st.success(f"{selected_subject}の欠席を記録しました！")
        st.rerun()

def absence_status():
    """欠席状況確認ページ"""
    st.header("📊 欠席状況確認")
    
    subjects = load_subjects()
    absences = load_absences()
    
    if not subjects:
        st.warning("まず科目を登録してください。")
        return
    
    # 統計情報の表示
    total_subjects = len(subjects)
    failed_subjects = 0
    warning_subjects = 0
    
    for subject, info in subjects.items():
        current_absences = len(absences.get(subject, []))
        max_absences = info['max_absences']
        
        if current_absences > max_absences:
            failed_subjects += 1
        elif max_absences - current_absences <= 1:
            warning_subjects += 1
    
    # サマリー表示
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("総科目数", total_subjects)
    with col2:
        st.metric("落単科目", failed_subjects, delta=f"-{failed_subjects}" if failed_subjects > 0 else None)
    with col3:
        st.metric("注意科目", warning_subjects, delta=f"-{warning_subjects}" if warning_subjects > 0 else None)
    with col4:
        safe_subjects = total_subjects - failed_subjects - warning_subjects
        st.metric("安全科目", safe_subjects, delta=f"+{safe_subjects}" if safe_subjects > 0 else None)
    
    st.divider()
    
    # 科目別欠席状況を表示
    for subject, info in subjects.items():
        current_absences = len(absences.get(subject, []))
        max_absences = info['max_absences']
        
        # 落単判定
        is_failed = current_absences > max_absences
        remaining = max_absences - current_absences
        
        # カードスタイルで表示
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 2])
            
            with col1:
                if is_failed:
                    st.markdown(f"### 🚨 {subject}")
                elif remaining <= 1:
                    st.markdown(f"### ⚠️ {subject}")
                else:
                    st.markdown(f"### ✅ {subject}")
            
            with col2:
                if is_failed:
                    st.error(f"落単確定: {current_absences}/{max_absences}回")
                    st.markdown("**単位取得不可**")
                else:
                    if remaining <= 1:
                        st.warning(f"危険: {current_absences}/{max_absences}回")
                        st.markdown(f"**残り{remaining}回まで**")
                    else:
                        st.success(f"安全: {current_absences}/{max_absences}回")
                        st.markdown(f"**残り{remaining}回**")
            
            with col3:
                progress = min(current_absences / max_absences, 1.0)
                if is_failed:
                    st.progress(1.0)
                    st.markdown("**進捗: 上限超過**")
                else:
                    st.progress(progress)
                    percentage = int(progress * 100)
                    st.markdown(f"**進捗: {percentage}%**")
            
            # 欠席履歴の表示
            if subject in absences and absences[subject]:
                with st.expander(f"{subject}の欠席履歴 ({len(absences[subject])}件)"):
                    # 欠席履歴を日付順でソート（新しい順）
                    sorted_absences = sorted(absences[subject], key=lambda x: x['date'], reverse=True)
                    
                    for i, record in enumerate(sorted_absences):
                        col_date, col_reason, col_delete = st.columns([2, 3, 1])
                        with col_date:
                            formatted_date = datetime.fromisoformat(record['date']).strftime('%Y/%m/%d (%a)')
                            st.write(formatted_date)
                        with col_reason:
                            reason_text = record['reason'] if record['reason'] else "理由なし"
                            st.write(reason_text)
                        with col_delete:
                            if st.button("削除", key=f"del_abs_{subject}_{i}"):
                                absences[subject].remove(record)
                                save_absences(absences)
                                st.rerun()
            else:
                st.info(f"{subject}の欠席記録はありません")
            
            st.divider()

def timetable_view():
    """時間割表示ページ"""
    st.header("📅 時間割表示")
    
    subjects = load_subjects()
    absences = load_absences()
    
    if not subjects:
        st.warning("まず科目を登録してください。")
        return
    
    # 表示形式の選択
    display_mode = st.radio(
        "表示形式を選択",
        ["カレンダー表示", "曜日別表示"],
        horizontal=True
    )
    
    if display_mode == "カレンダー表示":
        calendar_view(subjects, absences)
    else:
        weekday_view(subjects, absences)

def calendar_view(subjects, absences):
    """カレンダー表示機能"""
    # 月選択
    col1, col2 = st.columns(2)
    with col1:
        selected_year = st.selectbox("年", range(2020, 2030), index=5)  # 2025がデフォルト
    with col2:
        selected_month = st.selectbox("月", range(1, 13), index=datetime.now().month - 1)
    
    # 科目フィルター
    st.subheader("表示する科目を選択")
    selected_subjects = st.multiselect(
        "科目を選択（空の場合は全科目表示）",
        list(subjects.keys()),
        default=list(subjects.keys())
    )
    
    if not selected_subjects:
        selected_subjects = list(subjects.keys())
    
    # カレンダー表示
    cal = calendar.monthcalendar(selected_year, selected_month)
    
    st.subheader(f"{selected_year}年{selected_month}月の欠席状況")
    
    # 凡例
    st.markdown("""
    **凡例:**
    - 🚫 欠席あり
    - ⚠️ 落単危険科目の欠席
    - 🚨 落単確定科目の欠席
    """)
    
    # カレンダーのスタイル設定
    st.markdown("""
    <style>
    .calendar-day {
        border: 1px solid #ddd;
        padding: 10px;
        min-height: 100px;
        background-color: #f9f9f9;
    }
    .calendar-day-header {
        font-weight: bold;
        text-align: center;
        background-color: #e0e0e0;
        padding: 5px;
    }
    .absence-item {
        font-size: 0.8em;
        margin: 2px 0;
        padding: 2px 4px;
        border-radius: 3px;
    }
    .absence-normal {
        background-color: #ffeb3b;
        color: #333;
    }
    .absence-warning {
        background-color: #ff9800;
        color: white;
    }
    .absence-danger {
        background-color: #f44336;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 曜日ヘッダー
    days = ['月', '火', '水', '木', '金', '土', '日']
    cols = st.columns(7)
    for i, day in enumerate(days):
        cols[i].markdown(f'<div class="calendar-day-header">{day}</div>', unsafe_allow_html=True)
    
    # カレンダーの各週を表示
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].markdown('<div class="calendar-day"></div>', unsafe_allow_html=True)
            else:
                # その日の欠席情報を取得
                date_str = f"{selected_year}-{selected_month:02d}-{day:02d}"
                absent_subjects_info = []
                
                for subject in selected_subjects:
                    if subject in absences:
                        for absence in absences[subject]:
                            if absence['date'] == date_str:
                                # 科目の状態を判定
                                current_absences = len(absences[subject])
                                max_absences = subjects[subject]['max_absences']
                                
                                if current_absences > max_absences:
                                    status = "danger"
                                    icon = "🚨"
                                elif max_absences - current_absences <= 1:
                                    status = "warning"
                                    icon = "⚠️"
                                else:
                                    status = "normal"
                                    icon = "🚫"
                                
                                absent_subjects_info.append({
                                    'subject': subject,
                                    'status': status,
                                    'icon': icon,
                                    'reason': absence.get('reason', '')
                                })
                
                # 日付と欠席科目を表示
                day_content = f'<div class="calendar-day"><strong>{day}</strong><br>'
                
                if absent_subjects_info:
                    for info in absent_subjects_info:
                        reason_text = f" ({info['reason']})" if info['reason'] else ""
                        day_content += f'<div class="absence-item absence-{info["status"]}">{info["icon"]} {info["subject"]}{reason_text}</div>'
                
                day_content += '</div>'
                cols[i].markdown(day_content, unsafe_allow_html=True)
    
    # 月間統計
    st.subheader(f"{selected_year}年{selected_month}月の統計")
    
    monthly_stats = {}
    for subject in selected_subjects:
        count = 0
        if subject in absences:
            for absence in absences[subject]:
                absence_date = datetime.fromisoformat(absence['date'])
                if absence_date.year == selected_year and absence_date.month == selected_month:
                    count += 1
        monthly_stats[subject] = count
    
    if any(count > 0 for count in monthly_stats.values()):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**科目別欠席回数:**")
            for subject, count in monthly_stats.items():
                if count > 0:
                    current_total = len(absences.get(subject, []))
                    max_absences = subjects[subject]['max_absences']
                    
                    if current_total > max_absences:
                        st.error(f"🚨 {subject}: {count}回 (総計: {current_total}/{max_absences})")
                    elif max_absences - current_total <= 1:
                        st.warning(f"⚠️ {subject}: {count}回 (総計: {current_total}/{max_absences})")
                    else:
                        st.info(f"🚫 {subject}: {count}回 (総計: {current_total}/{max_absences})")
        
        with col2:
            total_monthly_absences = sum(monthly_stats.values())
            st.metric("月間総欠席回数", total_monthly_absences)
            
            # 最も欠席の多い科目
            if monthly_stats:
                max_subject = max(monthly_stats, key=monthly_stats.get)
                if monthly_stats[max_subject] > 0:
                    st.metric("最多欠席科目", max_subject, monthly_stats[max_subject])
    else:
        st.success(f"{selected_year}年{selected_month}月は欠席がありませんでした！")

def weekday_view(subjects, absences):
    """曜日別表示機能"""
    st.subheader("曜日別欠席状況")
    
    # 科目フィルター
    selected_subjects = st.multiselect(
        "表示する科目を選択（空の場合は全科目表示）",
        list(subjects.keys()),
        default=list(subjects.keys()),
        key="weekday_subjects"
    )
    
    if not selected_subjects:
        selected_subjects = list(subjects.keys())
    
    # 曜日別の欠席データを集計
    weekday_names = ['月曜日', '火曜日', '水曜日', '木曜日', '金曜日', '土曜日', '日曜日']
    weekday_data = {day: {} for day in weekday_names}
    
    for subject in selected_subjects:
        if subject in absences:
            for absence in absences[subject]:
                absence_date = datetime.fromisoformat(absence['date'])
                weekday = weekday_names[absence_date.weekday()]
                
                if subject not in weekday_data[weekday]:
                    weekday_data[weekday][subject] = []
                
                weekday_data[weekday][subject].append({
                    'date': absence['date'],
                    'reason': absence.get('reason', '')
                })
    
    # 曜日別表示
    for weekday in weekday_names:
        with st.expander(f"📅 {weekday}", expanded=True):
            if weekday_data[weekday]:
                for subject, absence_list in weekday_data[weekday].items():
                    # 科目の状態を判定
                    current_absences = len(absences.get(subject, []))
                    max_absences = subjects[subject]['max_absences']
                    
                    if current_absences > max_absences:
                        status_icon = "🚨"
                        status_text = "落単確定"
                        status_color = "red"
                    elif max_absences - current_absences <= 1:
                        status_icon = "⚠️"
                        status_text = "注意"
                        status_color = "orange"
                    else:
                        status_icon = "✅"
                        status_text = "安全"
                        status_color = "green"
                    
                    st.markdown(f"**{status_icon} {subject}** ({status_text}) - {len(absence_list)}回欠席")
                    
                    # 欠席詳細を表示
                    for absence in absence_list:
                        formatted_date = datetime.fromisoformat(absence['date']).strftime('%Y/%m/%d')
                        reason_text = f" - {absence['reason']}" if absence['reason'] else ""
                        st.write(f"　• {formatted_date}{reason_text}")
                    
                    st.divider()
            else:
                st.info(f"{weekday}に欠席した科目はありません")
    
    # 曜日別統計
    st.subheader("曜日別統計")
    
    weekday_stats = {}
    for weekday in weekday_names:
        total_absences = sum(len(absence_list) for absence_list in weekday_data[weekday].values())
        weekday_stats[weekday] = total_absences
    
    # 統計をグラフ風に表示
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**曜日別欠席回数:**")
        for weekday, count in weekday_stats.items():
            if count > 0:
                st.write(f"• {weekday}: {count}回")
            else:
                st.write(f"• {weekday}: 0回")
    
    with col2:
        if any(count > 0 for count in weekday_stats.values()):
            max_weekday = max(weekday_stats, key=weekday_stats.get)
            min_weekday = min(weekday_stats, key=weekday_stats.get)
            
            st.metric("最多欠席曜日", max_weekday, weekday_stats[max_weekday])
            st.metric("最少欠席曜日", min_weekday, weekday_stats[min_weekday])
        else:
            st.info("欠席データがありません")

if __name__ == "__main__":
    main()

