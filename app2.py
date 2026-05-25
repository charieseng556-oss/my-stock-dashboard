import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
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

# 🌟 數據源：逐一抓取權值股
@st.cache_data(ttl=1800)
def build_custom_heatmap():
    stocks_data = {
        "Ticker": [
            "MSFT", "AAPL", "NVDA", "GOOGL", "AMZN", "META", "AVGO",
            "TSLA", "NFLX", "AMD", "INTC", "QCOM",
            "JPM", "BAC", "V", "MA",
            "XOM", "CVX", "LLY", "JNJ", "WMT", "COST"
        ],
        "Sector": [
            "Technology", "Technology", "Technology", "Communication", "Consumer Cyclical", "Communication", "Technology",
            "Consumer Cyclical", "Communication", "Technology", "Technology", "Technology",
            "Financial", "Financial", "Financial", "Financial",
            "Energy", "Energy", "Healthcare", "Healthcare", "Consumer Defensive", "Consumer Defensive"
        ],
        "Industry": [
            "Software", "Hardware", "Semiconductors", "Internet", "Retail", "Internet", "Semiconductors",
            "Automotive", "Entertainment", "Semiconductors", "Semiconductors", "Semiconductors",
            "Banking", "Banking", "Credit Services", "Credit Services",
            "Oil & Gas", "Oil & Gas", "Pharma", "Pharma", "Retail", "Retail"
        ]
    }
    
    rows = []
    for i, ticker in enumerate(stocks_data["Ticker"]):
        try:
            stock_obj = yf.Ticker(ticker)
            hist = stock_obj.history(period="2d")
            
            if len(hist) >= 2:
                close_t = hist['Close'].iloc[-1]
                close_y = hist['Close'].iloc[-2]
                pct_change = ((close_t - close_y) / close_y) * 100
                
                market_cap = 500000000000 if ticker in ["MSFT", "AAPL", "NVDA", "GOOGL", "AMZN"] else 100000000000
                try:
                    market_cap = stock_obj.info.get("marketCap", market_cap)
                except:
                    pass
                
                # 美化 Label 顯示：加上正號提示，讓排版向原廠靠攏
                prefix = "+" if pct_change > 0 else ""
                label_text = f"{ticker}<br>{prefix}{round(pct_change, 2)}%"
                
                rows.append({
                    "Ticker": ticker,
                    "Sector": stocks_data["Sector"][i],
                    "Industry": stocks_data["Industry"][i],
                    "Pct_Change": round(pct_change, 2),
                    "Market_Cap": market_cap,
                    "Label": label_text
                })
        except:
            continue
            
    return pd.DataFrame(rows)

# 3. 網頁佈局
col_left, col_right = st.columns([1.3, 1.5])

# === 左半邊：數字大盤與自製熱力圖 ===
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
    
    # 呈現自製熱力圖
    st.subheader("🗺️ 自製美股權值股熱力圖 (台股高質感配色)")
    with st.spinner("正在即時繪製美股板塊地圖..."):
        df_heatmap = build_custom_heatmap()
        
        if not df_heatmap.empty:
            # 建立樹狀圖
            fig = px.treemap(
                df_heatmap,
                path=['Sector', 'Industry', 'Label'],
                values='Market_Cap',
                color='Pct_Change',
                # 🌟 視覺升級點：擴充更具層次感的台股紅綠漸層配色 (鮮綠 -> 暗綠 -> 黑 -> 暗紅 -> 鮮紅)
                color_continuous_scale=[
                    [0.0, '#00B050'],   # 大跌鮮綠
                    [0.4, '#1C2920'],   # 微跌暗綠
                    [0.5, '#181818'],   # 平盤深黑
                    [0.6, '#331C1C'],   # 微漲暗紅
                    [1.0, '#FF4B4B']    # 大漲鮮紅
                ],
                color_continuous_midpoint=0,
                template="plotly_dark"  # 🌟 使用內建暗色主題，確保字體色彩維持高對比與美觀
            )
            
            # 安全調整排版：僅微調邊距與背景，不觸碰會報錯的文字內聯引數
            fig.update_layout(
                margin=dict(t=25, l=10, r=10, b=10), # 給上方分類標籤留出呼吸空間
                height=530,
                coloraxis_showscale=False,
                paper_bgcolor='rgba(0,0,0,0)',       # 背景透明融合網頁
                plot_bgcolor='rgba(0,0,0,0)'
            )
            
            # 渲染互動圖表
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            st.write("💡 *滑鼠移到方塊上可看詳情，點擊板塊方塊可局部放大。*")
        else:
            st.warning("暫時無法即時繪製熱力圖，請重新整理網頁。")


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
