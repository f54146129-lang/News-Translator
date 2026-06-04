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
    
    # 3. 核心功能：翻譯處理與進階單字分類
    with st.spinner("正在進行智慧翻譯與單字萃取..."):
        # 翻譯內文
        translated_text = GoogleTranslator(source='en', target=target_lang).translate(english_text)
        
        # 利用正規表達式抓出所有單字
        raw_words = re.findall(r'\b[A-Za-z]+\b', english_text)
        
        # 初始化分類清單
        proper_nouns = set()
        easy_words = set()
        med_words = set()
        hard_words = set()

        for w in raw_words:
            # 排除太短的無意義字詞 (如 a, is, to)
            if len(w) <= 2:
                continue
                
            # 判斷專有名詞 (字首大寫)
            if w.istitle():
                proper_nouns.add(w)
            else:
                w_lower = w.lower()
                # 依長度分級
                if 3 <= len(w_lower) <= 5:
                    easy_words.add(w_lower)
                elif 6 <= len(w_lower) <= 8:
                    med_words.add(w_lower)
                elif len(w_lower) >= 9:
                    hard_words.add(w_lower)

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
    
   # 5. 進階加分功能：分級單字卡 (使用 Tabs 設計)
    st.subheader("💡 智慧單字庫 (Smart Vocabulary)")
    
    # 建立四個標籤頁
    tab1, tab2, tab3, tab4 = st.tabs(["🟢 簡單 (Easy)", "🟡 中等 (Medium)", "🔴 困難 (Hard)", "🏛️ 專有名詞 (Proper Nouns)"])
    
    # 定義一個建立單字卡的輔助函數
    def create_word_cards(word_set):
        if not word_set:
            st.write("此篇新聞未偵測到此層級的單字。")
            return
            
        words_to_show = list(word_set)[:10] 
        cols = st.columns(4) # 一排顯示 4 個單字
        
        for idx, word in enumerate(words_to_show):
            with cols[idx % 4]:
                try:
                    word_trans = GoogleTranslator(source='en', target=target_lang).translate(word)
                    st.metric(label=word, value=word_trans)
                except:
                    st.metric(label=word, value="翻譯加載中...")

    # 將分類好的單字填入對應的標籤頁
    with tab1:
        create_word_cards(easy_words)
    with tab2:
        create_word_cards(med_words)
    with tab3:
        create_word_cards(hard_words)
    with tab4:
        create_word_cards(proper_nouns)

except Exception as e:
    st.error(f"系統暫時無法連線，請檢查網路設定。錯誤訊息: {e}")
