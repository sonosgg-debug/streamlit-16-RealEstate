import socket
socket.setdefaulttimeout(5.0)

import os
import glob
import datetime
import pandas as pd
import numpy as np
import yfinance as yf

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KB_DATA_DIR = os.path.join(BASE_DIR, "KBData")
CACHE_DIR = os.path.join(BASE_DIR, "data_cache")
STOCK_CACHE_FILE = os.path.join(CACHE_DIR, "stock_monthly_historical.csv")
COMBINED_CACHE_FILE = os.path.join(CACHE_DIR, "combined_monthly_data.parquet")
COMBINED_CSV_FILE = os.path.join(CACHE_DIR, "combined_monthly_data.csv")

TARGET_REGIONS = ["강남11개구", "강북14개구", "수도권", "전국"]
DISPLAY_COLUMNS = ["강남11개구", "강북14개구", "수도권", "전국", "KOSPI", "S&P 500"]

def get_latest_kb_file():
    """Find the latest KB Excel file in KBData directory"""
    if not os.path.exists(KB_DATA_DIR):
        os.makedirs(KB_DATA_DIR, exist_ok=True)
        return None
    
    excel_files = glob.glob(os.path.join(KB_DATA_DIR, "*.xlsx")) + glob.glob(os.path.join(KB_DATA_DIR, "*.xls"))
    if not excel_files:
        return None
    
    # Sort by modification time descending
    excel_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return excel_files[0]

def parse_kb_excel(file_path):
    """
    Parse KB Real Estate monthly apartment sales price index Excel.
    Extracts '강남11개구', '강북14개구', '수도권', '전국'.
    Returns DataFrame indexed by Timestamp (YYYY-MM-01).
    """
    if not file_path or not os.path.exists(file_path):
        return None
    
    try:
        df_raw = pd.read_excel(file_path)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None
    
    first_col = df_raw.columns[0]
    # Filter target rows
    df_filtered = df_raw[df_raw[first_col].isin(TARGET_REGIONS)].copy()
    if df_filtered.empty:
        return None
    
    # Set region name as index
    df_filtered.set_index(first_col, inplace=True)
    
    # Transpose so dates become the index and regions become columns
    df_kb = df_filtered.T
    
    # Parse dates from column headers
    valid_dates = []
    valid_rows = []
    for col_name in df_kb.index:
        try:
            if isinstance(col_name, (pd.Timestamp, datetime.datetime, datetime.date)):
                d = pd.to_datetime(col_name)
            else:
                # String parsing e.g. '1986-01-01 09:00:52' or '1986.01' or '1986-01'
                d = pd.to_datetime(str(col_name).strip())
            # Normalize to 1st day of month
            norm_d = pd.Timestamp(year=d.year, month=d.month, day=1)
            valid_dates.append(norm_d)
            valid_rows.append(col_name)
        except Exception:
            continue
            
    df_kb_clean = df_kb.loc[valid_rows].copy()
    df_kb_clean.index = valid_dates
    
    # Replace '-' or other non-numeric with NaN, then convert to float
    for col in TARGET_REGIONS:
        if col in df_kb_clean.columns:
            df_kb_clean[col] = df_kb_clean[col].replace('-', np.nan)
            df_kb_clean[col] = pd.to_numeric(df_kb_clean[col], errors='coerce')
        else:
            df_kb_clean[col] = np.nan
            
    df_kb_clean = df_kb_clean[TARGET_REGIONS]
    df_kb_clean.sort_index(inplace=True)
    df_kb_clean = df_kb_clean[~df_kb_clean.index.duplicated(keep='last')]
    return df_kb_clean

def _ensure_krx_credentials():
    """Load KRX credentials from environment or 00 API Key directory if needed"""
    if os.environ.get('KRX_ID') and os.environ.get('KRX_PW'):
        return True
    candidate_paths = [
        os.path.join(BASE_DIR, ".env"),
        os.path.join(os.path.dirname(BASE_DIR), "00 API Key", "KRX ID&PW.txt")
    ]
    for p in candidate_paths:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    for line in f:
                        if "ID :" in line or "ID:" in line:
                            os.environ['KRX_ID'] = line.split(":")[-1].strip()
                        elif "PW :" in line or "PW:" in line:
                            os.environ['KRX_PW'] = line.split(":")[-1].strip()
                if os.environ.get('KRX_ID') and os.environ.get('KRX_PW'):
                    return True
            except Exception:
                pass
    return False

def update_stock_cache():
    """
    Fetch and/or update KOSPI and S&P 500 monthly data.
    Uses cached historical file and appends recent months if available.
    """
    os.makedirs(CACHE_DIR, exist_ok=True)
    _ensure_krx_credentials()
    
    # 1. Check existing cache
    df_existing = None
    if os.path.exists(STOCK_CACHE_FILE):
        try:
            df_existing = pd.read_csv(STOCK_CACHE_FILE, index_col=0, parse_dates=True)
            df_existing.index = pd.to_datetime(df_existing.index).to_period('M').to_timestamp()
        except Exception:
            df_existing = None

    # 2. Fetch S&P 500 via yfinance
    try:
        sp_dl = yf.download('^GSPC', start='1986-01-01', interval='1mo', progress=False)
        if isinstance(sp_dl.columns, pd.MultiIndex):
            sp_close = sp_dl['Close'].iloc[:, 0]
        else:
            sp_close = sp_dl['Close']
        sp_monthly = pd.Series(sp_close.values, index=sp_close.index.to_period('M').to_timestamp(), name='S&P 500')
    except Exception as e:
        print(f"Error fetching S&P 500: {e}")
        sp_monthly = df_existing['S&P 500'] if df_existing is not None and 'S&P 500' in df_existing else pd.Series(dtype=float)

    # 3. KOSPI update
    kospi_monthly = None
    # If existing cache has complete KOSPI up to recent, fetch only latest chunk
    if df_existing is not None and 'KOSPI' in df_existing and not df_existing['KOSPI'].dropna().empty:
        kospi_monthly = df_existing['KOSPI'].copy()
        last_date = kospi_monthly.dropna().index[-1]
        now = pd.Timestamp.now()
        # If cache is older than current month, fetch recent
        if (now.year > last_date.year) or (now.month > last_date.month):
            s_str = (last_date - pd.DateOffset(months=1)).strftime('%Y%m%d')
            e_str = now.strftime('%Y%m%d')
            updated = False
            # 1. Try FinanceDataReader first (fast, works on AWS/Cloud without IP blocks)
            try:
                import FinanceDataReader as fdr
                df_fdr = fdr.DataReader('KS11', (last_date - pd.DateOffset(months=1)).strftime('%Y-%m-%d'), now.strftime('%Y-%m-%d'))
                if df_fdr is not None and not df_fdr.empty and 'Close' in df_fdr.columns:
                    m_fdr = df_fdr['Close'].resample('ME').last()
                    m_fdr.index = m_fdr.index.to_period('M').to_timestamp()
                    kospi_monthly = kospi_monthly.combine_first(m_fdr)
                    updated = True
            except Exception as e:
                print(f"FDR update failed: {e}")

            # 2. If FDR failed, try pykrx with timeout protection
            if not updated:
                try:
                    from pykrx import stock
                    df_recent = stock.get_index_ohlcv_by_date(s_str, e_str, "1001")
                    if df_recent is not None and not df_recent.empty:
                        m_recent = df_recent['종가'].resample('ME').last()
                        m_recent.index = m_recent.index.to_period('M').to_timestamp()
                        kospi_monthly = kospi_monthly.combine_first(m_recent)
                except Exception as e:
                    print(f"Error updating recent KOSPI via pykrx: {e}")
    else:
        # Full build KOSPI
        try:
            import FinanceDataReader as fdr
            df_all = fdr.DataReader('KS11', '1986-01-01')
            if df_all is not None and not df_all.empty and 'Close' in df_all.columns:
                m_all = df_all['Close'].resample('ME').last()
                m_all.index = m_all.index.to_period('M').to_timestamp()
                kospi_monthly = m_all
                kospi_monthly.name = 'KOSPI'
        except Exception as e:
            print(f"Error building full KOSPI via FDR: {e}")
            try:
                from pykrx import stock
                chunks = []
                for start_yr in range(1986, 2027, 5):
                    end_yr = min(datetime.date.today().year, start_yr + 4)
                    s_date = f"{start_yr}0101"
                    e_date = f"{end_yr}1231"
                    try:
                        df_c = stock.get_index_ohlcv_by_date(s_date, e_date, "1001")
                        if df_c is not None and not df_c.empty:
                            m_c = df_c['종가'].resample('ME').last()
                            chunks.append(m_c)
                    except Exception:
                        pass
                if chunks:
                    kospi_monthly = pd.concat(chunks)
                    kospi_monthly.index = kospi_monthly.index.to_period('M').to_timestamp()
                    kospi_monthly.name = 'KOSPI'
            except Exception as e2:
                print(f"Error building full KOSPI via pykrx: {e2}")

    # Combine KOSPI and S&P 500
    df_stocks = pd.DataFrame({'KOSPI': kospi_monthly, 'S&P 500': sp_monthly})
    df_stocks.sort_index(inplace=True)
    df_stocks = df_stocks[~df_stocks.index.duplicated(keep='last')]
    df_stocks.to_csv(STOCK_CACHE_FILE)
    return df_stocks

def get_stock_data():
    """Load stock data from cache, or update if missing"""
    if os.path.exists(STOCK_CACHE_FILE):
        try:
            df = pd.read_csv(STOCK_CACHE_FILE, index_col=0, parse_dates=True)
            df.index = pd.to_datetime(df.index).to_period('M').to_timestamp()
            return df
        except Exception:
            pass
    return update_stock_cache()

def load_combined_data(force_update=False):
    """
    Load combined dataset of 6 indicators:
    '강남11개구', '강북14개구', '수도권', '전국', 'KOSPI', 'S&P 500'.
    
    Returns:
        df_combined (pd.DataFrame): Monthly data indexed by Timestamp
        metadata (dict): Info about the data source, latest date, file name, etc.
    """
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    latest_file = get_latest_kb_file()
    if latest_file is None:
        return None, {"error": "KBData 폴더에 엑셀 파일이 존재하지 않습니다."}
        
    kb_mod_time = os.path.getmtime(latest_file)
    kb_file_name = os.path.basename(latest_file)
    
    # Check if cache exists and is fresh
    if not force_update and os.path.exists(COMBINED_CSV_FILE):
        try:
            df_cache = pd.read_csv(COMBINED_CSV_FILE, index_col=0, parse_dates=True)
            df_cache.index = pd.to_datetime(df_cache.index).to_period('M').to_timestamp()
            cache_mod_time = os.path.getmtime(COMBINED_CSV_FILE)
            
            # If cache is newer than KB excel file, return cached data
            if cache_mod_time >= kb_mod_time:
                metadata = {
                    "kb_file_name": kb_file_name,
                    "kb_file_mtime": datetime.datetime.fromtimestamp(kb_mod_time).strftime('%Y-%m-%d %H:%M:%S'),
                    "start_date": df_cache.index[0].strftime('%Y-%m'),
                    "end_date": df_cache.index[-1].strftime('%Y-%m'),
                    "total_months": len(df_cache),
                    "from_cache": True
                }
                return df_cache, metadata
        except Exception as e:
            print(f"Error reading combined cache: {e}")
            
    # Rebuild combined data
    df_kb = parse_kb_excel(latest_file)
    if df_kb is None or df_kb.empty:
        return None, {"error": f"KB 엑셀 파일({kb_file_name}) 파싱에 실패했습니다."}
        
    df_stocks = get_stock_data()
    if force_update:
        df_stocks = update_stock_cache()
        
    # Merge on month index
    # Use outer join to keep all dates, but restrict to start from 1986-01-01
    df_combined = df_kb.join(df_stocks, how='outer')
    df_combined = df_combined.loc['1986-01-01':]
    
    # Reorder columns to user specification
    cols = [c for c in DISPLAY_COLUMNS if c in df_combined.columns]
    df_combined = df_combined[cols]
    
    # Save cache
    df_combined.to_csv(COMBINED_CSV_FILE)
    try:
        df_combined.to_parquet(COMBINED_CACHE_FILE)
    except Exception:
        pass
        
    metadata = {
        "kb_file_name": kb_file_name,
        "kb_file_mtime": datetime.datetime.fromtimestamp(kb_mod_time).strftime('%Y-%m-%d %H:%M:%S'),
        "start_date": df_combined.index[0].strftime('%Y-%m'),
        "end_date": df_combined.index[-1].strftime('%Y-%m'),
        "total_months": len(df_combined),
        "from_cache": False
    }
    return df_combined, metadata

def save_uploaded_kb_file(uploaded_file):
    """Save an uploaded Streamlit file to KBData folder and trigger rebuild"""
    if uploaded_file is None:
        return False, "업로드된 파일이 없습니다."
    
    os.makedirs(KB_DATA_DIR, exist_ok=True)
    file_path = os.path.join(KB_DATA_DIR, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
        
    # Rebuild combined cache
    df, meta = load_combined_data(force_update=True)
    if df is not None:
        return True, f"'{uploaded_file.name}' 저장 및 데이터 업데이트 완료!"
    else:
        return False, meta.get("error", "데이터 업데이트 실패")

def get_latest_expected_trading_day(target_date: str = None) -> str:
    """
    가장 최근 거래 완료된 실제 영업일 YYYY-MM-DD 반환.
    - target_date가 전달된 경우: 해당 날짜 기준 (또는 직전 영업일)
    - target_date가 없는 경우: KST 기준 15:45 이전이거나 오늘이 주말/새벽이면 직전 마감 거래일 반환
    """
    from datetime import datetime, timezone, timedelta
    now_kst = datetime.now(timezone(timedelta(hours=9)))
    if target_date:
        try:
            clean_date = str(target_date).replace('-', '')
            dt = datetime.strptime(clean_date, "%Y%m%d").replace(tzinfo=timezone(timedelta(hours=9)))
        except Exception:
            dt = now_kst
    else:
        dt = now_kst

    # 평일 15:45 이후에만 당일 종가 확정
    if dt.weekday() < 5 and (dt.hour > 15 or (dt.hour == 15 and dt.minute >= 45)):
        return dt.strftime("%Y-%m-%d")

    # 장전, 새벽, 주말: 직전 마감 거래일 산출
    if dt.weekday() == 0:    # 월요일 장전 -> 지난주 금요일 (3일 전)
        days_back = 3
    elif dt.weekday() == 6:  # 일요일 -> 지난주 금요일 (2일 전)
        days_back = 2
    elif dt.weekday() == 5:  # 토요일 -> 지난주 금요일 (1일 전)
        days_back = 1
    else:                    # 화~금 장전/새벽 -> 전일 (1일 전)
        days_back = 1

    return (dt - timedelta(days=days_back)).strftime("%Y-%m-%d")
