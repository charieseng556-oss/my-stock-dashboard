import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
from google import genai

# 1. 網頁基本設定
st.set_page_config(page_title="全球盤前 AI 戰情室", page_icon="🔮", layout="wide")

# 注入 CSS 讓 metric 顯示符合台灣習慣 (紅漲綠跌)
st.markdown("""
<style>
    div[data-testid="stMetricDelta"] > div svg { display: none; }
    div[data-testid="stMetricDelta"] > div { color: #FF4B4B !important; }
    div[data-testid="stMetricDelta"] > div:contains("-") { color: #00B050 !important; }
    [data-testid="stSidebar"] { display: none; }
</style>
""", unsafe_allow_html=True)

st.title("🔮 全球股市盤前 AI 戰情室")
st.write(f"系統檢查時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 2. 自動從後台秘密環境變數中讀取 API 金鑰
api_key = st.secrets.get("GEMINI_API_KEY")

# 3. 網頁佈局
col_left, col_right = st.columns([1.3, 1.5])

# === 左半邊：數字大盤與 Finviz 官方即時大圖 ===
with col_left:
    st.subheader("📈 主要市場昨日表現")
    market_tickers = {"S&P 500 指數": "^GSPC", "費城半導體": "^SOX", "台積電 ADR": "TSM", "輝達 NVDA": "NVDA"}
    results = []
    for name, ticker in market_tickers.items():
        try:
            hist = yf.Ticker(ticker).history(period="2d")
            pct = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
            results.append({"項目": name, "價格": round(hist['Close'].iloc[-1], 2), "漲跌幅(%)": round(pct, 2)})
        except: pass
    
    if results:
        metric_cols = st.columns(4)
        for idx, row in enumerate(results):
            with metric_cols[idx]:
                prefix = "+" if row["漲跌幅(%)"] > 0 else ""
                st.metric(label=row["項目"], value=row["價格"], delta=f"{prefix}{row['漲跌幅(%)']}%")
    
    st.divider()
    
    # 🌟 視覺終極改進：直接顯示 Finviz 官方渲染好的高密度全股熱力圖大圖 (100%不報錯、免嵌入)
    st.subheader("🗺️ S&P 500 前一營業日板塊熱力圖")
    
    # Finviz 官方每日更新的高畫質地圖圖片 URL
    finviz_heatmap_image = "https://finviz.com"
    
    # 透過 Streamlit 直接渲染圖檔，寬度自動滿版
    st.image(finviz_heatmap_image, use_container_width=True)
    
    # 提供一個按鈕，方便您隨時點過去看原廠會動的網頁
    st.link_button("🔗 點此開啟 Finviz 原廠互動網頁版", "https://finviz.com", use_container_width=True)


# === 右半邊：AI 盤前消息與板塊分析 ===
with col_right:
    st.subheader("📰 AI 盤前重點消息與板塊分析")
    if not api_key:
        st.error("❌ 系統未偵測到內建 API 金鑰！")
    else:
        with st.spinner("AI 秘書正透過 Google 搜尋昨晚最新財經大事..."):
            try:
                client = genai.Client(api_key=api_key)
                prompt = """
                請你使用內建的 Google 搜尋工具，搜尋以下主題最新、過去 24 小時內的新聞與動態：
                1. 「美股 最新消息 財經 大盤」
                2. 「美股 領漲 板塊 科技股 財報」
                3. 「輝達 NVIDIA Nvidia 晶片 科技新聞」
                4. 「SpaceX Tesla 馬斯克 最新動態」
                5. 「聯準會 Fed 利率 官員談話」
                
                結合你搜尋到的真實最新內容，為台灣投資人撰寫今天早上 08:30 的「全球盤前重點消息總覽」。
                
                【寫作與排版嚴格規範】
                1. 必須使用「台灣繁體中文」與台灣財經術語。
                2. 內文中的關鍵專有名詞、數據（例如：H100、20%、華許、CPI等）必須使用 **粗體** 標記。
                3. 每條新聞開頭必須加上一個對應的「功能性 Emoji」（例如：🇺🇸、🔥、💰、📈）。
                4. 標題前後絕對不要加上星號或斜體。嚴格依照下方格式與指定的三大區塊輸出：
                
                ### 核心市場消息
                - 
                - 
                
                ### 科技與企業動態（含昨日美股熱門板塊分析）
                - 
                - 
                
                ### 本週關注焦點
                - 
                """
                response = client.models.generate_content(
                    model='gemini-2.5-flash', contents=prompt, config={'tools': [{'google_search': {}}]} 
                )
                st.markdown(response.text)
            except Exception as e:
                st.error(f"AI 摘要生成失敗: {e}")
