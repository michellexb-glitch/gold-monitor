"""
黄金投资监控系统 V3.3
顶部核心对比区域 + 双坐标轴趋势图
"""

import streamlit as st
import yfinance as yf
from fredapi import Fred
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np

# ============ 页面配置 ============
st.set_page_config(
    page_title="黄金监控",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 现代化CSS样式
st.markdown("""
<style>
    /* 全局样式 */
    .main .block-container {
        padding: 1rem 1rem 2rem 1rem;
        max-width: 900px;
    }
    
    /* 隐藏Streamlit默认元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 标题样式 */
    h1 {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        margin-bottom: 0.3rem !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* 核心指标区域 */
    .core-metrics {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        padding: 1.2rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    .core-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 1rem;
        margin-bottom: 1rem;
    }
    
    .core-item {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 12px;
        padding: 0.8rem;
    }
    
    .core-label {
        font-size: 0.85rem;
        color: #666;
        margin-bottom: 0.3rem;
    }
    
    .core-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #2c3e50;
    }
    
    .core-change {
        font-size: 0.75rem;
        font-weight: 600;
        margin-top: 0.2rem;
    }
    
    /* 卡片容器 */
    .metric-card {
        background: white;
        border-radius: 16px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border: 1px solid rgba(0,0,0,0.05);
    }
    
    /* 头部行 */
    .metric-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.8rem;
    }
    
    .metric-title {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .metric-emoji {
        font-size: 1.3rem;
    }
    
    .metric-name {
        font-size: 0.95rem;
        color: #666;
        font-weight: 500;
    }
    
    .metric-date {
        font-size: 0.75rem;
        color: #999;
        white-space: nowrap;
    }
    
    /* 数值行 */
    .metric-values {
        display: flex;
        align-items: baseline;
        gap: 1rem;
        margin-bottom: 0.8rem;
        flex-wrap: nowrap;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #2c3e50;
        white-space: nowrap;
    }
    
    .change-badge {
        padding: 0.25rem 0.7rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        white-space: nowrap;
        flex-shrink: 0;
    }
    
    .change-positive {
        background: #d4edda;
        color: #155724;
    }
    
    .change-negative {
        background: #f8d7da;
        color: #721c24;
    }
    
    .change-neutral {
        background: #e2e3e5;
        color: #383d41;
    }
    
    /* 分隔线 */
    .section-divider {
        border-top: 2px solid #e0e0e0;
        margin: 2rem 0 1.5rem 0;
    }
    
    /* 移动端适配 */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 0.5rem 0.8rem 1rem 0.8rem;
        }
        
        .core-grid {
            grid-template-columns: 1fr;
            gap: 0.8rem;
        }
        
        .core-value {
            font-size: 1.3rem;
        }
        
        .metric-value {
            font-size: 1.8rem;
        }
        
        h1 {
            font-size: 1.5rem !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# ============ 数据获取 ============

@st.cache_data(ttl=3600)
def fetch_data(fred_key, days=90):
    """获取6个核心指标"""
    data = {}
    errors = []
    
    # FRED数据
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
    
    # Yahoo Finance数据
    try:
        end = datetime.now()
        start = end - timedelta(days=days)
        
        tickers = {
            'GC=F': '黄金价格',
            'DX-Y.NYB': '美元指数',
            '^VIX': 'VIX恐慌指数'
        }
        
        for ticker, name in tickers.items():
            try:
                df = yf.download(ticker, start=start, end=end, progress=False)
                if not df.empty and 'Close' in df.columns:
                    data[name] = df['Close'].squeeze()
            except Exception as e:
                errors.append(f"{name}: {str(e)}")
            
    except Exception as e:
        errors.append(f"Yahoo: {str(e)}")
    
    if not data:
        return pd.DataFrame(), errors
    
    try:
        df = pd.DataFrame(data)
        return df, errors
    except Exception as e:
        errors.append(f"数据合并错误: {str(e)}")
        return pd.DataFrame(), errors

# ============ 主界面 ============

# 标题
st.markdown("<h1>💰 黄金监控</h1>", unsafe_allow_html=True)
update_time = datetime.now().strftime('%m/%d %H:%M')
st.caption(f"🕐 {update_time} 更新")

# 侧边栏配置
with st.sidebar:
    st.subheader("⚙️ 配置")
    fred_key = st.text_input(
        "FRED API",
        value="08adf813c05015a73196c5338e2fec76",
        type="password"
    )

# 获取数据
with st.spinner('加载中...'):
    df, errors = fetch_data(fred_key)

if errors:
    with st.expander("⚠️ 警告"):
        for e in errors:
            st.caption(e)

if df.empty:
    st.error("数据获取失败，请稍后刷新")
    st.stop()

# ============ 核心对比区域 ============

core_metrics_data = [
    ('黄金价格', '🏆', '$/oz'),
    ('美元指数', '💵', ''),
    ('实际利率', '📉', '%'),
    ('VIX恐慌指数', '⚡', '')
]

# 构建核心指标HTML
core_html = '<div class="core-metrics"><div class="core-grid">'

for name, emoji, unit in core_metrics_data:
    if name in df.columns:
        series = df[name].dropna()
        if len(series) > 0:
            current = series.iloc[-1]
            
            # 计算30日变化
            days_back = min(30, len(series) - 1)
            if days_back > 0:
                previous = series.iloc[-days_back-1]
                change_pct = ((current - previous) / previous * 100) if previous != 0 else 0
            else:
                change_pct = 0
            
            change_symbol = "↑" if change_pct > 0 else "↓" if change_pct < 0 else "→"
            change_color = "#27ae60" if change_pct > 0 else "#e74c3c" if change_pct < 0 else "#95a5a6"
            
            core_html += f'''
            <div class="core-item">
                <div class="core-label">{emoji} {name}</div>
                <div class="core-value">{current:.2f}{unit}</div>
                <div class="core-change" style="color: {change_color};">
                    {change_symbol} {abs(change_pct):.2f}% 30日
                </div>
            </div>
            '''

core_html += '</div></div>'
st.markdown(core_html, unsafe_allow_html=True)

# ============ 双坐标趋势图 ============

# 图1: 黄金 vs VIX
if '黄金价格' in df.columns and 'VIX恐慌指数' in df.columns:
    gold = df['黄金价格'].dropna()
    vix = df['VIX恐慌指数'].dropna()
    
    # 对齐数据
    common_idx = gold.index.intersection(vix.index)
    gold_aligned = gold.loc[common_idx]
    vix_aligned = vix.loc[common_idx]
    
    fig1 = make_subplots(specs=[[{"secondary_y": True}]])
    
    # 黄金（左轴）
    fig1.add_trace(
        go.Scatter(
            x=common_idx,
            y=gold_aligned,
            name="黄金",
            line=dict(color='#f39c12', width=2.5),
            hovertemplate='黄金: $%{y:.2f}<extra></extra>'
        ),
        secondary_y=False
    )
    
    # VIX（右轴）
    fig1.add_trace(
        go.Scatter(
            x=common_idx,
            y=vix_aligned,
            name="VIX",
            line=dict(color='#e74c3c', width=2.5),
            hovertemplate='VIX: %{y:.2f}<extra></extra>'
        ),
        secondary_y=True
    )
    
    fig1.update_layout(
        title="🏆 黄金 vs ⚡ VIX恐慌指数",
        title_font=dict(size=14),
        height=280,
        margin=dict(l=10, r=10, t=40, b=30),
        hovermode='x unified',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        )
    )
    
    fig1.update_xaxes(showgrid=True, gridcolor='rgba(128,128,128,0.1)')
    fig1.update_yaxes(title_text="黄金 ($/oz)", secondary_y=False, showgrid=True, gridcolor='rgba(128,128,128,0.1)')
    fig1.update_yaxes(title_text="VIX", secondary_y=True, showgrid=False)
    
    st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})

# 图2: 美元指数 vs 实际利率
if '美元指数' in df.columns and '实际利率' in df.columns:
    dxy = df['美元指数'].dropna()
    real_rate = df['实际利率'].dropna()
    
    # 对齐数据
    common_idx = dxy.index.intersection(real_rate.index)
    dxy_aligned = dxy.loc[common_idx]
    rate_aligned = real_rate.loc[common_idx]
    
    fig2 = make_subplots(specs=[[{"secondary_y": True}]])
    
    # 美元指数（左轴）
    fig2.add_trace(
        go.Scatter(
            x=common_idx,
            y=dxy_aligned,
            name="美元指数",
            line=dict(color='#27ae60', width=2.5),
            hovertemplate='美元指数: %{y:.2f}<extra></extra>'
        ),
        secondary_y=False
    )
    
    # 实际利率（右轴）
    fig2.add_trace(
        go.Scatter(
            x=common_idx,
            y=rate_aligned,
            name="实际利率",
            line=dict(color='#3498db', width=2.5),
            hovertemplate='实际利率: %{y:.2f}%<extra></extra>'
        ),
        secondary_y=True
    )
    
    fig2.update_layout(
        title="💵 美元指数 vs 📉 实际利率",
        title_font=dict(size=14),
        height=280,
        margin=dict(l=10, r=10, t=40, b=30),
        hovermode='x unified',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        )
    )
    
    fig2.update_xaxes(showgrid=True, gridcolor='rgba(128,128,128,0.1)')
    fig2.update_yaxes(title_text="美元指数", secondary_y=False, showgrid=True, gridcolor='rgba(128,128,128,0.1)')
    fig2.update_yaxes(title_text="实际利率 (%)", secondary_y=True, showgrid=False)
    
    st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})

# ============ 分隔线 ============
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
st.subheader("📊 完整数据")

# ============ 详细数据展示 ============

metrics = [
    ('黄金价格', '$/盎司', '🏆', '#f39c12'),
    ('美元指数', '', '💵', '#27ae60'),
    ('VIX恐慌指数', '', '⚡', '#e74c3c'),
    ('实际利率', '%', '📉', '#3498db'),
    ('通胀预期', '%', '📈', '#9b59b6'),
    ('名义利率', '%', '📊', '#34495e')
]

for name, unit, emoji, color in metrics:
    if name in df.columns:
        series = df[name].dropna()
        if len(series) == 0:
            continue
            
        current = series.iloc[-1]
        latest_date = series.index[-1].strftime('%Y/%m/%d')
        
        # 计算30日变化
        days_back = min(30, len(series) - 1)
        if days_back > 0:
            previous = series.iloc[-days_back-1]
            change = current - previous
            change_pct = (change / previous * 100) if previous != 0 else 0
        else:
            change_pct = 0
        
        change_class = "change-positive" if change_pct > 0 else "change-negative" if change_pct < 0 else "change-neutral"
        change_symbol = "↑" if change_pct > 0 else "↓" if change_pct < 0 else "→"
        
        # 卡片HTML
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-header">
                <div class="metric-title">
                    <span class="metric-emoji">{emoji}</span>
                    <span class="metric-name">{name}</span>
                </div>
                <span class="metric-date">{latest_date}</span>
            </div>
            <div class="metric-values">
                <span class="metric-value">{current:.2f}{unit}</span>
                <span class="change-badge {change_class}">{change_symbol} {abs(change_pct):.2f}% 30日</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 单指标趋势图
        chart_data = series.reset_index()
        chart_data.columns = ['日期', '数值']
        
        base_value = previous if days_back > 0 else series.iloc[0]
        chart_data['变化率'] = ((chart_data['数值'] - base_value) / base_value * 100).round(2)
        
        # 智能纵轴
        data_min = chart_data['数值'].min()
        data_max = chart_data['数值'].max()
        data_range = data_max - data_min
        
        if data_range / data_min < 0.05:
            margin = data_range * 2
            y_min = data_min - margin
            y_max = data_max + margin
        elif data_range / data_min < 0.15:
            margin = data_range * 0.5
            y_min = data_min - margin
            y_max = data_max + margin
        else:
            y_min = 0
            y_max = data_max * 1.1
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=chart_data['日期'],
            y=chart_data['数值'],
            mode='lines',
            name=name,
            line=dict(color=color, width=2.5),
            fill='tozeroy',
            fillcolor=f'rgba{tuple(list(bytes.fromhex(color[1:])) + [0.1])}',
            hovertemplate=(
                '<b>%{x|%Y-%m-%d}</b><br>' +
                f'{name}: %{{y:.2f}}{unit}<br>' +
                '相对30日前: %{customdata:+.2f}%' +
                '<extra></extra>'
            ),
            customdata=chart_data['变化率']
        ))
        
        fig.update_layout(
            height=160,
            margin=dict(l=10, r=10, t=5, b=5),
            xaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
            yaxis=dict(
                showticklabels=True,
                showgrid=True,
                gridcolor='rgba(128,128,128,0.1)',
                zeroline=False,
                range=[y_min, y_max],
                tickformat='.2f'
            ),
            hovermode='x unified',
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            dragmode=False
        )
        
        fig.update_xaxes(fixedrange=True)
        fig.update_yaxes(fixedrange=True)
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'staticPlot': False})
        
        st.markdown("<br>", unsafe_allow_html=True)

# ============ 底部 ============

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    csv = df.to_csv().encode('utf-8')
    st.download_button(
        "📥 导出数据",
        csv,
        f"gold_{datetime.now():%Y%m%d}.csv",
        "text/csv",
        use_container_width=True
    )

with col2:
    with st.popover("ℹ️ 说明", use_container_width=True):
        st.markdown("""
        **核心对比区域**
        - 双坐标图展示关联指标
        - 黄金与VIX通常正相关
        - 美元与利率影响黄金走势
        
        **数据来源**
        - FRED: 利率数据
        - Yahoo: 黄金、美元、VIX
        """)

st.caption("⚠️ 仅供参考，不构成投资建议")
