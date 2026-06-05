
import streamlit as st
import feedparser
from deep_translator import GoogleTranslator
import re
import requests
from bs4 import BeautifulSoup

# 設定網頁為寬螢幕佈局
st.set_page_config(layout="wide", page_title="國際時事雙語網")

st.title("🌐 國際時事雙語閱讀與單字擴充網")
st.caption("期末專案成果發表 - 智慧語言學習系統")
st.write("---")

# 1. 抓取 RSS 新聞摘要
@st.cache_data(ttl=600)
def fetch_bbc_news():
    url = "http://feeds.bbci.co.uk/news/world/rss.xml"
    feed = feedparser.parse(url)
    return feed.entries[:8]

# 🌟 新增：自動順著網址去抓取「真實文章內文」的爬蟲函數
@st.cache_data(ttl=600)
def fetch_article_main_content(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # BBC 新聞段落通常包在 <p> 標籤內，我們抓取所有段落
        paragraphs = soup.find_all('p')
        # 過濾掉太短的版權宣告或無意義字串
        valid_p = [p.text for p in paragraphs if len(p.text) > 30]
        
        # 取前 4 個有實質內容的段落作為「大致內容」
        main_content = " \n\n".join(valid_p[:4])
        return main_content if main_content else "無法自動抓取此篇新聞內文，請點擊上方連結閱讀。"
    except:
        return "擷取原文內容失敗。"

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
    
    selected_entry = next(e for e in entries if e.title == selected_title)
    english_text = selected_entry.summary
    news_link = selected_entry.link
    
 # 3. 核心功能：翻譯處理與進階單字分類
    with st.spinner("系統正在進行智慧翻譯與深度內文擷取..."):
        # 翻譯原本的短摘要
        translated_text = GoogleTranslator(source='en', target=target_lang).translate(english_text)
        
        # 抓取並翻譯文章大致內容
        full_content_en = fetch_article_main_content(news_link)
        try:
            full_content_trans = GoogleTranslator(source='en', target=target_lang).translate(full_content_en[:3000])
        except:
            full_content_trans = "內文翻譯失敗或超過字數限制。"

        # 🌟 關鍵修改 1：建立「停用詞 (Stop Words)」黑名單，排除常見無意義單字
        stop_words = {"the", "and", "that", "have", "for", "not", "with", "this", "but", "his", "from", "they", "will", "would", "there", "their", "what", "about", "who", "which", "when", "can", "could", "them", "only", "its", "also", "then", "than", "other", "some", "very", "just", "into", "your", "our", "were", "been", "has", "had", "are", "was", "out", "two", "end", "said"}

        # 🌟 關鍵修改 2：改從「完整內文 (full_content_en)」抓取單字，基數變大，單字才會豐富！
        raw_words = re.findall(r'\b[A-Za-z]+\b', full_content_en)
        
        proper_nouns = set()
        easy_words = set()
        med_words = set()
        hard_words = set()

        for w in raw_words:
            w_lower = w.lower()
            
            # 過濾掉長度小於 3 的單字，或是存在於黑名單中的單字
            if len(w) <= 3 or w_lower in stop_words:
                continue
                
            if w.istitle():
                proper_nouns.add(w)
            else:
                # 🌟 關鍵修改 3：提高字母長度門檻，讓單字更具挑戰性
                if 4 <= len(w_lower) <= 6:
                    easy_words.add(w_lower)
                elif 7 <= len(w_lower) <= 9:
                    med_words.add(w_lower)
                elif len(w_lower) >= 10:
                    hard_words.add(w_lower)

    # 4. 前端畫面呈現：頭條對照
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📰 頭條摘要 (Headline Summary)")
        st.info(english_text)
        st.caption(f"🔗 [點擊這裡前往 BBC 閱讀完整原文]({news_link})")
        
    with col2:
        st.subheader("🎓 摘要翻譯 (Translation)")
        st.success(translated_text)

    st.write("---")
    
    # 🌟 新增區塊：使用「摺疊面板 (Expander)」來顯示長篇的大致內容
    st.subheader("📄 文章大致內容 (Article Overview)")
    with st.expander("👉 點擊展開：查看原文前段內容與全文翻譯", expanded=False):
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**原文摘錄 (前四段)：**")
            st.write(full_content_en)
        with col_b:
            st.markdown(f"**大致內容翻譯 ({lang_option.split(' ')[0]})：**")
            st.write(full_content_trans)

    st.write("---")
    
    # 5. 分級單字卡
    st.subheader("💡 智慧單字庫 (Smart Vocabulary)")
    tab1, tab2, tab3, tab4 = st.tabs(["🟢 簡單 (Easy)", "🟡 中等 (Medium)", "🔴 困難 (Hard)", "🏛️ 專有名詞 (Proper Nouns)"])
    
    def create_word_cards(word_set):
        if not word_set:
            st.write("此篇摘要未偵測到此層級的單字。")
            return
        words_to_show = list(word_set)[:10] 
        cols = st.columns(4)
        for idx, word in enumerate(words_to_show):
            with cols[idx % 4]:
                try:
                    word_trans = GoogleTranslator(source='en', target=target_lang).translate(word)
                    st.metric(label=word, value=word_trans)
                except:
                    st.metric(label=word, value="翻譯加載中...")

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
