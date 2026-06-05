import streamlit as st
import feedparser
from deep_translator import GoogleTranslator
import re
from collections import Counter
from newspaper import Article

# 設定網頁為寬螢幕佈局
st.set_page_config(layout="wide", page_title="國際時事雙語網")

st.title("🌐 國際時事雙語閱讀與單字擴充網")
st.caption(" 智慧語言學習系統")
st.write("---")

# 🌟 新增：定義不同類別的 BBC RSS 頻道網址字典
RSS_FEEDS = {
    "🇬🇧 BBC 國際與政治": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "🇺🇸 CNN 國際頭條": "http://rss.cnn.com/rss/edition.rss",
    "🇬🇧 BBC 科學與環境": "http://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
    "🇺🇸 CNN 科技新聞": "http://rss.cnn.com/rss/edition_technology.rss",
    "🇬🇧 BBC 生活與健康": "http://feeds.bbci.co.uk/news/health/rss.xml"
}

# 1. 抓取 RSS 新聞摘要 (🌟 修改：加入 url 參數，讓它可以抓不同類別)
@st.cache_data(ttl=600)
def fetch_bbc_news(url):
    feed = feedparser.parse(url)
    return feed.entries[:8]

@st.cache_data(ttl=600)
def fetch_universal_article_content(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        paragraphs = article.text.split('\n')
        valid_p = [p.strip() for p in paragraphs if len(p.strip()) > 30]
        main_content = " \n\n".join(valid_p[:4])
        return main_content if main_content else "無法自動抓取此篇新聞內文，請點擊上方連結閱讀。"
    except Exception as e:
        return "擷取原文內容失敗，可能是該網站具有反爬蟲機制。"

try:
    # 2. 側邊欄控制項
    st.sidebar.header("⚙️ 控制面板")
    
    # 🌟 新增：讓使用者先選擇「新聞類別」
    selected_category = st.sidebar.selectbox("📂 請選擇新聞類別：", list(RSS_FEEDS.keys()))
    
    # 根據選定的類別，找出對應的 RSS 網址並抓取新聞
    feed_url = RSS_FEEDS[selected_category]
    entries = fetch_bbc_news(feed_url)
    titles = [e.title for e in entries]
    
    # 🌟 接著才讓使用者選擇該類別下的「頭條新聞」
    selected_title = st.sidebar.selectbox("📰 請選擇頭條新聞：", titles)
    
    lang_option = st.sidebar.radio(
        "🗣️ 請選擇目標學習語言：",
        ["法文 (French)", "繁體中文 (Traditional Chinese)"]
    )
    target_lang = 'fr' if "法文" in lang_option else 'zh-TW'
    
    selected_entry = next(e for e in entries if e.title == selected_title)
    english_text = selected_entry.summary
    news_link = selected_entry.link
    
    # 3. 核心功能：翻譯處理與進階單字分類
    with st.spinner(f"系統正在擷取【{selected_category.split(' ')[0]}】最新資訊與智慧翻譯..."):
        translated_text = GoogleTranslator(source='en', target=target_lang).translate(english_text)
        
        full_content_en = fetch_universal_article_content(news_link)
        try:
            full_content_trans = GoogleTranslator(source='en', target=target_lang).translate(full_content_en[:3000])
        except:
            full_content_trans = "內文翻譯失敗或超過字數限制。"

        # 停用詞黑名單 (過濾掉無意義的常見字)
        stop_words = {"the", "and", "that", "have", "for", "not", "with", "this", "but", "his", "from", "they", "will", "would", "there", "their", "what", "about", "who", "which", "when", "can", "could", "them", "only", "its", "also", "then", "than", "other", "some", "very", "just", "into", "your", "our", "were", "been", "has", "had", "are", "was", "out", "two", "end", "said", "more", "over", "after"}

        raw_words = re.findall(r'\b[A-Za-z]+\b', full_content_en)
        
        proper_nouns = set()
        easy_words = set()
        med_words = set()
        hard_words = set()
        valid_words_for_freq = [] # 🌟 新增：用來收集有意義的單字，準備計算頻率

        for w in raw_words:
            w_lower = w.lower()
            if len(w) <= 3 or w_lower in stop_words:
                continue
                
            # 收集用來計算頻率的有效單字
            valid_words_for_freq.append(w_lower)

            if w.istitle():
                proper_nouns.add(w)
            else:
                if 4 <= len(w_lower) <= 6:
                    easy_words.add(w_lower)
                elif 7 <= len(w_lower) <= 9:
                    med_words.add(w_lower)
                elif len(w_lower) >= 10:
                    hard_words.add(w_lower)

        # 🌟 核心新功能：詞頻分析 (Term Frequency)，抓取該篇文章的主題核心字
        word_counts = Counter(valid_words_for_freq)
        # 取出出現頻率最高的 12 個單字
        top_domain_words = [word for word, count in word_counts.most_common(12)]

    # 4. 前端畫面呈現
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📰 頭條摘要 (Headline Summary)")
        st.info(english_text)
        st.caption(f"🔗 [點擊這裡前往 BBC 閱讀完整原文]({news_link})")
        
    with col2:
        st.subheader("🎓 摘要翻譯 (Translation)")
        st.success(translated_text)

    st.write("---")
    
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
    
  # 5. 分級單字卡與語境分析
    st.subheader("💡 智慧單字庫與語境分析 (Smart Vocabulary & Context)")
    
    # 標籤頁更新
    tab0, tab1, tab2, tab3, tab4 = st.tabs(["🔥 領域焦點 (含原文例句)", "🟢 簡單", "🟡 中等", "🔴 困難", "🏛️ 專有名詞"])
    
    # 🌟 零風險高階功能：從文章中自動抓取包含該單字的原句
    def get_context_sentence(word, text):
        # 簡單地用句號切分文章
        sentences = text.split('.')
        for s in sentences:
            # 如果單字存在於這個句子中，就回傳整句話
            if re.search(r'\b' + re.escape(word) + r'\b', s, re.IGNORECASE):
                return s.strip() + "."
        return ""

    def create_word_cards(word_collection):
        if not word_collection:
            st.write("此篇新聞未偵測到此層級的單字。")
            return
        words_to_show = list(word_collection)[:12] 
        cols = st.columns(4)
        for idx, word in enumerate(words_to_show):
            with cols[idx % 4]:
                try:
                    word_trans = GoogleTranslator(source='en', target=target_lang).translate(word)
                    st.metric(label=word, value=word_trans)
                except:
                    st.metric(label=word, value="翻譯加載中...")

    # 🌟 將「領域焦點」升級為可展開的例句面板
    with tab0:
        st.markdown("##### 🎯 核心單字與新聞原句解析")
        for word in top_domain_words[:6]: # 抓前 6 個最重要的單字就好，保持版面清爽
            try:
                word_trans = GoogleTranslator(source='en', target=target_lang).translate(word)
                context_en = get_context_sentence(word, full_content_en)
                
                # 如果有找到原句，就順便翻譯原句並做成摺疊面板
                if context_en and len(context_en) > 5:
                    context_trans = GoogleTranslator(source='en', target=target_lang).translate(context_en)
                    with st.expander(f"✨ **{word}** 👉  {word_trans}"):
                        st.markdown(f"**📰 新聞原句：** {context_en}")
                        st.markdown(f"**💡 語境翻譯 ({lang_option.split(' ')[0]})：** {context_trans}")
                else:
                    st.metric(label=word, value=word_trans)
            except:
                pass

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
