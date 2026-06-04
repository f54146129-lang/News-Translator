import streamlit as st
import feedparser
from deep_translator import GoogleTranslator
import re

# 設定網頁為寬螢幕佈局
st.set_page_config(layout="wide", page_title="國際時事雙語網")

st.title("🌐 國際時事雙語閱讀與單字擴充網")
st.caption("期末專案成果發表 - 智慧語言學習系統")
st.write("---")

# 1. 抓取新聞 (使用 BBC World News RSS，避開反爬蟲，速度極快)
@st.cache_data(ttl=600) # 快取資料 10 分鐘，避免頻繁請求被鎖 IP
def fetch_bbc_news():
    url = "http://feeds.bbci.co.uk/news/world/rss.xml"
    feed = feedparser.parse(url)
    return feed.entries[:8]  # 取前 8 則最新頭條

try:
    entries = fetch_bbc_news()
    titles = [e.title for e in entries]
    
    # 2. 側邊欄控制項
    st.sidebar.header("⚙️ 控制面板")
    selected_title = st.sidebar.selectbox("請選擇今日頭條新聞：", titles)
    
    lang_option = st.sidebar.radio(
        "請選擇目標學習語言：",
        ["法文 (French)", "繁體中文 (Traditional Chinese)"]
    )
    target_lang = 'fr' if "法文" in lang_option else 'zh-TW'
    
    # 找到使用者選中的那則新聞
    selected_entry = next(e for e in entries if e.title == selected_title)
    english_text = selected_entry.summary
    
    # 3. 核心功能：翻譯處理
    with st.spinner("正在進行智慧翻譯與單字萃取..."):
        # 翻譯內文
        translated_text = GoogleTranslator(source='en', target=target_lang).translate(english_text)
        
        # 簡單的 NLP 邏輯：利用正規表達式篩選出長度大於 6 的英文單字作為「核心單字」
        all_words = re.findall(r'\b[a-zA-Z]{6,}\b', english_text)
        keywords = list(set([w.lower() for w in all_words]))[:4] # 取前 4 個不重複單字

    # 4. 前端畫面呈現：左右雙語對照
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📰 英文原文 (Original)")
        st.info(english_text)
        st.caption(f"🔗 [閱讀完整新聞]({selected_entry.link})")
        
    with col2:
        st.subheader("🎓 智慧翻譯 (Translation)")
        st.success(translated_text)

    st.write("---")
    
    # 5. 加分功能：核心單字卡
    st.subheader("💡 今日核心單字擴充 (Vocabulary)")
    if keywords:
        v_cols = st.columns(len(keywords))
        for idx, word in enumerate(keywords):
            with v_cols[idx]:
                # 自動查詢該單字的中文解釋
                word_cn = GoogleTranslator(source='en', target='zh-TW').translate(word)
                st.metric(label=f"單字 {idx+1}", value=word)
                st.markdown(f"**中文意：** {word_cn}")
    else:
        st.write("本篇新聞較簡短，未偵測到複雜核心單字。")

except Exception as e:
    st.error(f"系統暫時無法連線，請檢查網路設定。錯誤訊息: {e}")