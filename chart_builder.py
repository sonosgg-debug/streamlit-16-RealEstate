import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Color Palette for 6 indicators (optimized for dark theme #0f172a / #1e293b)
COLOR_PALETTE = {
    "강남11개구": "#f43f5e",   # Rose Red
    "강북14개구": "#fb923c",   # Vivid Orange
    "수도권":     "#a855f7",   # Vibrant Purple
    "전국":       "#38bdf8",   # Sky Blue
    "KOSPI":     "#eab308",   # Rich Gold / Amber
    "S&P 500":   "#22c55e",   # Emerald Green
}

LINE_DASH_MAP = {
    "강남11개구": "solid",
    "강북14개구": "solid",
    "수도권":     "solid",
    "전국":       "solid",
    "KOSPI":     "solid",
    "S&P 500":   "solid"
}

def calculate_returns(df_combined, start_date, end_date):
    """
    Slices data between start_date and end_date,
    and normalizes cumulative return (%) with start_date as 0%.
    
    Returns:
        df_returns (pd.DataFrame): Cumulative returns in percent
        df_sliced (pd.DataFrame): Sliced raw prices/indices
        notes (dict): Extra notices (e.g. Sudokwon start month)
    """
    if df_combined is None or df_combined.empty:
        return None, None, {}
    
    # Convert dates to Timestamp
    s_ts = pd.to_datetime(start_date).to_period('M').to_timestamp()
    e_ts = pd.to_datetime(end_date).to_period('M').to_timestamp()
    
    # Slice dataframe
    df_sliced = df_combined.loc[s_ts:e_ts].copy()
    if df_sliced.empty:
        return None, None, {}
    
    df_returns = pd.DataFrame(index=df_sliced.index)
    notes = {}
    
    for col in df_sliced.columns:
        series = df_sliced[col].dropna()
        if series.empty:
            df_returns[col] = np.nan
            continue
            
        # First available value in this sliced range
        first_valid_date = series.index[0]
        base_val = series.iloc[0]
        
        if first_valid_date > s_ts:
            notes[col] = f"'{col}' 데이터는 {first_valid_date.strftime('%Y년 %m월')}부터 제공되어 해당 시점을 0% 기준으로 계산합니다."
            
        # Cumulative return (%) = ((P_t / P_0) - 1) * 100 (rounded to 2 decimals)
        ret_series = np.round(((df_sliced[col] / base_val) - 1.0) * 100.0, 2)
        df_returns[col] = ret_series
        
    return df_returns, df_sliced, notes

def calculate_metrics(df_returns, df_sliced):
    """
    Calculates key investment performance metrics:
    - Base Date & Value
    - Final Date & Value
    - Total Cumulative Return (%)
    - CAGR (%)
    - Maximum Drawdown (MDD %)
    """
    if df_returns is None or df_sliced is None or df_returns.empty:
        return pd.DataFrame()
    
    metrics = []
    
    for col in df_returns.columns:
        ret_series = df_returns[col].dropna()
        raw_series = df_sliced[col].dropna()
        
        if ret_series.empty or raw_series.empty:
            continue
            
        start_dt = raw_series.index[0]
        end_dt = raw_series.index[-1]
        start_val = raw_series.iloc[0]
        end_val = raw_series.iloc[-1]
        total_ret = ret_series.iloc[-1]
        
        # Calculate years elapsed
        months_elapsed = (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month)
        years_elapsed = max(months_elapsed / 12.0, 1.0 / 12.0)
        
        # CAGR (%) = ((P_end / P_start) ** (1 / years) - 1) * 100
        if start_val > 0 and end_val > 0 and years_elapsed > 0:
            cagr = ((end_val / start_val) ** (1.0 / years_elapsed) - 1.0) * 100.0
        else:
            cagr = np.nan
            
        # Maximum Drawdown (MDD) based on raw prices
        cummax = raw_series.cummax()
        drawdown = (raw_series - cummax) / cummax * 100.0
        mdd = drawdown.min()
        
        # Best and Worst monthly return
        pct_monthly = raw_series.pct_change() * 100.0
        best_month = pct_monthly.max() if not pct_monthly.dropna().empty else np.nan
        worst_month = pct_monthly.min() if not pct_monthly.dropna().empty else np.nan
        
        metrics.append({
            "지표": col,
            "시작 기준월": start_dt.strftime('%Y-%m'),
            "시작 원본값": start_val,
            "최신 반영월": end_dt.strftime('%Y-%m'),
            "최종 원본값": end_val,
            "누적 수익률 (%)": total_ret,
            "CAGR (연평균 %)": cagr,
            "MDD (최대 낙폭 %)": mdd,
            "월간 최대상승 (%)": best_month,
            "월간 최대하락 (%)": worst_month,
        })
        
    df_metrics = pd.DataFrame(metrics)
    if not df_metrics.empty:
        # Sort by total return descending
        df_metrics.sort_values(by="누적 수익률 (%)", ascending=False, inplace=True)
        df_metrics.reset_index(drop=True, inplace=True)
        
    return df_metrics

def build_comparison_chart(df_returns, df_sliced):
    """
    Creates an interactive, visually stunning Plotly line chart
    with unified header tooltip (no duplicate dates), crosshairs, 0% baseline, and dark theme.
    """
    fig = go.Figure()
    
    if df_returns is None or df_returns.empty:
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#1E293B",
            plot_bgcolor="#0F172A",
            annotations=[{
                "text": "표시할 데이터가 없습니다.",
                "xref": "paper",
                "yref": "paper",
                "showarrow": False,
                "font": {"size": 16, "color": "#94a3b8"}
            }]
        )
        return fig
        
    for col in df_returns.columns:
        color = COLOR_PALETTE.get(col, "#ffffff")
        line_dash = LINE_DASH_MAP.get(col, "solid")
        
        y_vals = df_returns[col]
        raw_vals = df_sliced[col]
        
        # Pre-format text with indicator name and exactly 2 decimals
        text_list = []
        for y, r in zip(y_vals, raw_vals):
            if pd.isna(y):
                text_list.append("")
            else:
                sign = "+" if y > 0 else ""
                raw_str = f"{r:,.2f}" if pd.notna(r) else "-"
                text_list.append(f"<b>{col}</b>: <b>{sign}{y:,.2f}%</b> (지수 {raw_str})")
                
        fig.add_trace(go.Scatter(
            x=df_returns.index,
            y=y_vals,
            mode='lines',
            name=col,
            line=dict(color=color, width=2.5, dash=line_dash),
            text=text_list,
            hovertemplate="%{text}<extra></extra>",
            connectgaps=False
        ))
        
    # Activate secondary y-axis on the right so Plotly renders right-side tick labels
    fig.add_trace(go.Scatter(
        x=[None],
        y=[None],
        yaxis="y2",
        mode="markers",
        marker=dict(opacity=0, size=0),
        showlegend=False,
        hoverinfo="skip"
    ))
        
    # Add horizontal baseline at 0%
    fig.add_hline(
        y=0,
        line_width=1.5,
        line_dash="dash",
        line_color="rgba(255, 255, 255, 0.4)",
        annotation_text="0% (기준점)",
        annotation_position="bottom right",
        annotation_font=dict(color="rgba(255, 255, 255, 0.6)", size=11)
    )
    
    # Layout styling matching high-contrast Tailwind Slate standard
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#1E293B",
        plot_bgcolor="#0F172A",
        margin=dict(l=50, r=50, t=40, b=50),
        height=620,
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(30, 41, 59, 0.8)",
            bordercolor="#334155",
            borderwidth=1,
            font=dict(size=12, color="#f8fafc")
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor="#334155",
            gridwidth=1,
            zeroline=False,
            showline=True,
            linecolor="#475569",
            tickfont=dict(color="#cbd5e1", size=11),
            hoverformat="%Y년 %m월",
            showspikes=True,
            spikemode="across",
            spikesnap="cursor",
            spikethickness=1,
            spikedash="dot",
            spikecolor="#94a3b8"
        ),
        yaxis=dict(
            title=dict(text="누적 수익률 (%)", font=dict(color="#f8fafc", size=13)),
            showgrid=True,
            gridcolor="#334155",
            gridwidth=1,
            zeroline=False,
            showline=True,
            linecolor="#475569",
            ticksuffix="%",
            tickfont=dict(color="#cbd5e1", size=11),
            showspikes=True,
            spikemode="across",
            spikesnap="cursor",
            spikethickness=1,
            spikedash="dot",
            spikecolor="#94a3b8"
        ),
        yaxis2=dict(
            overlaying="y",
            side="right",
            matches="y",
            showgrid=False,
            zeroline=False,
            showline=True,
            linecolor="#475569",
            ticksuffix="%",
            tickfont=dict(color="#cbd5e1", size=11),
            showspikes=True,
            spikemode="across",
            spikesnap="cursor",
            spikethickness=1,
            spikedash="dot",
            spikecolor="#94a3b8"
        )
    )
    
    return fig
