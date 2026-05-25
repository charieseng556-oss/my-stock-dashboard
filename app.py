import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
from google import genai

# 1. 網頁基本設定
st.set_page_config(page_title="全球盤前 AI 戰情室", page_icon="🔮", layout="wide")
st.title("🔮 全球股市盤前 AI 戰情室")
st.write(f"系統檢查時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 2. 右側邊欄：設定您的 AI 金鑰（第一次使用需輸入）
st.sidebar.header("⚙️ 系統設定")
api_key = st.sidebar.text_input("輸入 Gemini API Key", type="password", help="請至 Google AI Studio 免費申請")

# 3. 左半邊：數字大盤數據
col_data, col_ai = st.columns([1, 1.5])

with col_data:
    st.subheader("📈 主要市場昨日表現")
    market_tickers = {
        "S&P 500 指數": "^GSPC",
        "費城半導體": "^SOX",
        "台積電 ADR": "TSM",
        "輝達 NVDA": "NVDA"
    }
    
    results = []
    for name, ticker in market_tickers.items():
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="2d")
            if len(hist) >= 2:
                close_t = hist['Close'].iloc[-1]
                close_y = hist['Close'].iloc[-2]
                change = close_t - close_y
                pct = (change / close_y) * 100
                results.append({"項目": name, "價格": round(close_t, 2), "漲跌幅(%)": round(pct, 2)})
        except:
            pass
            
    df = pd.DataFrame(results)
    if not df.empty:
        for _, row in df.iterrows():
            st.metric(label=row["項目"], value=row["價格"], delta=f"{row['漲跌幅(%)']}%")
    
    st.divider()
    st.write("💡 *數據每 5 分鐘自動刷新。*")

# 4. 右半邊：AI 盤前消息摘要
with col_ai:
    st.subheader("📰 AI 盤前重點消息總覽")
    
    if not api_key:
        st.info("🔑 請在左側欄位輸入您的 Gemini API 金鑰以啟動 AI 盤前摘要功能。")
    else:
        with st.spinner("AI 正在為您閱讀昨晚全球財經新聞，請稍候..."):
            try:
                                # 4-1. 改用 Google 新聞 RSS 抓取全球即時財經與美股焦點新聞
                import urllib.request
                import xml.etree.ElementTree as ET
                
                news_context = ""
                try:
                    # 抓取 Google News 的商業與財經專區新聞
                    url = "https://google.com"
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req) as response:
                        xml_data = response.read()
                    
                    root = ET.fromstring(xml_data)
                    # 抓取前 15 條最新的美股/全球重大財經新聞標題
                    for item in root.findall('.//item')[:15]:
                        title = item.find('title').text if item.find('title') is not None else ""
                        description = item.find('description').text if item.find('description') is not None else ""
                        news_context += f"標題: {title}\n摘要: {description}\n\n"
                except Exception as rss_err:
                    # 如果 RSS 失敗，備用方案：抓取個別個股新聞組合
                    news_context = ""
                    for tkr in ["^GSPC", "NVDA", "TSM"]:
                        try:
                            for n in yf.Ticker(tkr).news[:3]:
                                news_context += f"標題: {n.get('title')}\n"
                        except:
                            pass

                # 4-2. 呼叫新版 Google Gemini API 進行繁體中文分析
                client = genai.Client(api_key=api_key)

                prompt = f"""
                你是一位專業的華爾街財經分析師。請根據以下昨晚最新的美股新聞與市場資訊：
                
                {news_context}
                
                請為台灣投資人整理一份今天早上08:30的「盤前焦點摘要」。
                必須使用「台灣繁體中文」，語氣專業精煉，並嚴格依據以下結構輸出：
                
                ### 核心市場消息
                - 地緣政治與總經風險（例如談判進展、原油走勢）
                - 聯準會（Fed）最新動向與官員表態
                
                ### 科技與企業動態
                - AI需求與半導體/科技硬體最新進展（如輝達、台積電相關消息）
                - 傳統巨頭、車廠轉型或其他重大企業收購（如SpaceX、特斯拉、福特等）
                
                ### 本週關注焦點
                - 財報密集成交期與值得留意的代表性企業
                """
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash', # 使用最新且速度最快的模型
                    contents=prompt,
                )
                
                # 4-3. 渲染 AI 生成的精美 Markdown 內容
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"AI 摘要生成失敗，錯誤訊息: {e}")
