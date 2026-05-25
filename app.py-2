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

# 2. 自動從後台讀取 API 金鑰
api_key = st.secrets.get("GEMINI_API_KEY")

# 🌟 自製熱力圖數據源：定義 S&P 500 核心科技與權值股清單
@st.cache_data(ttl=3600)  # 每小時自動更新一次即可，避免開網頁太慢
def build_custom_heatmap():
    # 定義板塊、行業與股票代碼
    stocks_data = {
        "Ticker": [
            "MSFT", "AAPL", "NVDA", "GOOGL", "AMZN", "META", "AVGO", # 科技/通訊/消費
            "TSLA", "NFLX", "AMD", "INTC", "QCOM",                    # 汽車/半導體
            "JPM", "BAC", "V", "MA",                                  # 金融
            "XOM", "CVX", "LLY", "JNJ", "WMT", "COST"                 # 能源/醫療/民生
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
    
    # 批次向 yfinance 抓取昨日漲跌幅與市值
    tickers_str = " ".join(stocks_data["Ticker"])
    try:
        data = yf.download(tickers_str, period="2d", group_by="ticker", progress=False)
        rows = []
        for i, ticker in enumerate(stocks_data["Ticker"]):
            try:
                hist = data[ticker]
                close_t = hist['Close'].iloc[-1]
                close_y = hist['Close'].iloc[-2]
                pct_change = ((close_t - close_y) / close_y) * 100
                
                # 抓取市值作為方塊大小依據（若抓不到則用固定大小）
                info = yf.Ticker(ticker).info
                market_cap = info.get("marketCap", 100000000000)
                
                rows.append({
                    "Ticker": ticker,
                    "Sector": stocks_data["Sector"][i],
                    "Industry": stocks_data["Industry"][i],
                    "Pct_Change": round(pct_change, 2),
                    "Market_Cap": market_cap,
                    "Label": f"{ticker}<br>{round(pct_change, 2)}%"
                })
            except:
                pass
        return pd.DataFrame(rows)
    except:
        return pd.DataFrame()

# 3. 網頁佈局
col_left, col_right = st.columns([1.3, 1.5])

# === 左半邊：數字大盤與「自製互動熱力圖」 ===
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
    
    # 🌟 自製 Plotly Treemap 熱力圖呈現
    st.subheader("🗺️ 自製美股權值股熱力圖 (台股配色)")
    with st.spinner("正在即時繪製美股板塊地圖..."):
        df_heatmap = build_custom_heatmap()
        
        if not df_heatmap.empty:
            # 建立 Plotly 樹狀圖
            fig = px.treemap(
                df_heatmap,
                path=['Sector', 'Industry', 'Label'], # 階層結構：板塊 -> 行業 -> 股票代碼
                values='Market_Cap',                  # 方塊大小由市值決定
                color='Pct_Change',                   # 顏色由漲跌幅決定
                color_continuous_scale=[[0, '#00B050'], [0.5, '#222222'], [1, '#FF4B4B']], # 綠色(跌) -> 暗色(平) -> 紅色(漲)
                color_continuous_midpoint=0
            )
            
            # 美化圖表排版
            fig.update_layout(
                margin=dict(t=10, l=10, r=10, b=10),
                height=500,
                coloraxis_showscale=False # 隱藏側邊顏色條，保持乾淨
            )
            fig.update_traces(textposition="inside", textfont_size=14)
            
            # 在網頁渲染互動圖表
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
