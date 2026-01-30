"""
黄金投资监控 - 精简版
只显示5个核心数据指标
"""

import streamlit as st
import yfinance as yf
from fredapi import Fred
import pandas as pd
from datetime import datetime, timedelta

# ============ 页面配置 ============
st.set_page_config(
    page_title="黄金数据监控",
    page_icon="💰",
    layout="centered"
)

# ============ 数据获取 ============

@st.cache_data(ttl=3600)  # 缓存1小时
def fetch_data(fred_key, days=90):
    """获取核心5个指标"""
    data = {}
    errors = []
    
    # 1. FRED数据
    try:
        fred = Fred(api_key=fred_key)
        start = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        series = {
            'DGS10': '名义利率',
            'T10YIE': '通胀预期',
            'DFII10': '实际利率'
        }
        
        for code, name in series.items():
            try:
                s = fred.get_series(code, start)
                if s is not None and not s.empty:
                    data[name] = s
            except Exception as e:
                errors.append(f"{name}: {str(e)}")
    except Exception as e:
        errors.append(f"FRED: {str(e)}")
    
    # 2. Yahoo Finance数据
    try:
        end = datetime.now()
        start = end - timedelta(days=days)
        
        # 黄金
        try:
            gold = yf.download('GC=F', start=start, end=end, progress=False)
            if not gold.empty:
                data['黄金价格'] = gold['Close']
        except Exception as e:
            errors.append(f"黄金: {str(e)}")
        
        # 美元指数
        try:
            dxy = yf.download('DX-Y.NYB', start=start, end=end, progress=False)
            if not dxy.empty:
                data['美元指数'] = dxy['Close']
        except Exception as e:
            errors.append(f"美元指数: {str(e)}")
            
    except Exception as e:
        errors.append(f"Yahoo: {str(e)}")
    
    df = pd.DataFrame(data) if data else pd.DataFrame()
    return df, errors

# ============ 主界面 ============

st.title("💰 黄金数据监控")
st.caption("核心5指标实时追踪")

# API密钥（可在侧边栏修改）
fred_key = st.sidebar.text_input(
    "FRED API密钥",
    value="08adf813c05015a73196c5338e2fec76",
    type="password"
)

# 获取数据
with st.spinner('加载数据...'):
    df, errors = fetch_data(fred_key)

# 显示更新时间
st.caption(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')} | 数据缓存1小时")

# 错误提示
if errors:
    with st.expander("⚠️ 数据获取警告"):
        for e in errors:
            st.caption(e)

if df.empty:
    st.error("❌ 暂时无法获取数据")
    st.info("💡 可能原因：网络问题或API频率限制，请稍后刷新")
    st.stop()

# ============ 数据显示 ============

st.markdown("---")

# 定义显示顺序和格式
metrics = [
    ('黄金价格', '$/盎司', '🏆'),
    ('美元指数', '', '💵'),
    ('名义利率', '%', '📊'),
    ('通胀预期', '%', '📈'),
    ('实际利率', '%', '📉')
]

# 显示数据卡片
for name, unit, emoji in metrics:
    if name in df.columns:
        series = df[name].dropna()
        if len(series) > 0:
            current = series.iloc[-1]
            
            # 计算变化（30日或可用天数）
            days_back = min(30, len(series) - 1)
            if days_back > 0:
                previous = series.iloc[-days_back-1]
                change = current - previous
                change_pct = (change / previous * 100) if previous != 0 else 0
            else:
                change = 0
                change_pct = 0
            
            # 显示
            with st.container():
                col1, col2 = st.columns([3, 2])
                
                with col1:
                    st.markdown(f"### {emoji} {name}")
                    st.markdown(f"<h2 style='margin:0; color: #1f77b4;'>{current:.2f}{unit}</h2>", unsafe_allow_html=True)
                
                with col2:
                    st.metric(
                        label=f"{days_back}日变化",
                        value="",
                        delta=f"{change_pct:+.2f}%"
                    )
                
                # 最新日期
                st.caption(f"📅 最新数据: {series.index[-1].date()}")
                st.markdown("---")

# ============ 数据表格 ============

with st.expander("📋 查看完整数据表"):
    # 只显示最近30天
    recent = df.tail(30).sort_index(ascending=False)
    recent.index = recent.index.date
    st.dataframe(recent, use_container_width=True)

# ============ 下载数据 ============

st.markdown("---")
csv = df.to_csv().encode('utf-8')
st.download_button(
    "📥 下载CSV数据",
    csv,
    f"gold_data_{datetime.now():%Y%m%d}.csv",
    "text/csv",
    use_container_width=True
)

# ============ 说明 ============

with st.expander("ℹ️ 数据说明"):
    st.markdown("""
    **数据来源：**
    - 黄金价格、美元指数：Yahoo Finance
    - 利率数据：FRED (美联储经济数据库)
    
    **更新频率：**
    - 黄金、美元：每个交易日更新
    - 利率数据：FRED官方更新频率
    
    **数据延迟：**
    - 缓存1小时，减少API请求
    - 刷新页面可获取最新数据
    
    **关键关系：**
    - 实际利率 ≈ 名义利率 - 通胀预期
    - 实际利率↑ → 黄金通常↓
    - 美元指数↑ → 黄金通常↓
    """)

st.caption("⚠️ 仅供参考，不构成投资建议")
