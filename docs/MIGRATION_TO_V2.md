# Migration Guide: v1.x to v2.0

## Overview

klse-screener-py v2.0 introduces structured dict-based functions to replace the legacy string-returning functions. This guide helps you migrate your code.

## Why the Change?

**v1.x functions** return formatted strings designed for LLM consumption:
```python
# v1.x (LEGACY)
result = get_klse_quarterly_history("5132.KL")
print(result)  # Formatted table string
```

**v2.0 functions** return structured dicts for programmatic use:
```python
# v2.0 (NEW)
result = get_klse_quarterly_financials_dict("5132.KL")
print(result["ttm_revenue"])  # 997200000.0
```

## Deprecation Timeline

| Version | Status | Date |
|---------|--------|------|
| 1.3.0 | Deprecation warnings added | 2026-04 |
| 1.4.0 | Deprecation warnings enforced | 2026-06 |
| 2.0.0 | Legacy functions removed | 2026-09 |

## Function Mapping

### Quarterly Financials

**Before (v1.x):**
```python
from klse_screener import get_klse_quarterly_history

result = get_klse_quarterly_history("5132.KL")
# Returns: Formatted string (for LLMs)
```

**After (v2.0):**
```python
from klse_screener import get_klse_quarterly_financials_dict

result = get_klse_quarterly_financials_dict("5132.KL")
# Returns: Dict with structured data
print(result["ttm_revenue"])       # 997200000.0
print(result["ttm_net_profit"])    # 71100000.0
print(result["quarterly_data"])    # List[Dict]
```

### Annual Financials

**Before (v1.x):**
```python
from klse_screener import get_klse_annual

result = get_klse_annual("5132.KL")
# Returns: Formatted string (for LLMs)
```

**After (v2.0):**
```python
from klse_screener import get_klse_annual_financials_dict

result = get_klse_annual_financials_dict("5132.KL")
# Returns: Dict with structured data
print(result["annual_data"])  # List[Dict]
```

### Fundamentals

**No change required!** The existing `get_klse_fundamentals()` function already returns a dict.

However, for Magic Formula users, the new `get_klse_fundamentals_combined()` includes TTM calculations and MF approximations:

```python
from klse_screener import get_klse_fundamentals_combined

result = get_klse_fundamentals_combined("5132.KL")
print(result["approx_ebit_ttm"])     # 71100000.0
print(result["approx_fixed_assets"]) # 1.24
```

### Price History

**Before (v1.x):**
```python
# No direct function - users had to scrape manually
```

**After (v2.0):**
```python
from klse_screener import scrape_ohlcv_raw

data = scrape_ohlcv_raw("5132.KL", period="30d")
# Returns: List[Dict] (pandas-free)
print(data[0])  # {"date": "2026-04-20", "open": 1.27, ...}
```

For pandas users (beatit-specific wrapper):
```python
# In beatit only - library is pandas-free
from app.api.data_sources.klsescreener_fundamentals import fetch_from_klsescreener

df = fetch_from_klsescreener("5132.KL")
# Returns: pd.DataFrame
```

## Migration Checklist

### For LLM/FinGenius Users

If you're using the library for LLM consumption (FinGenius):

- [ ] **Keep using string functions** for now (they still work in v1.3.0)
- [ ] Update by v1.4.0 when warnings become errors
- [ ] Consider migrating to structured data + custom formatting

**Example migration:**
```python
# OLD (v1.x)
from klse_screener import get_klse_quarterly_history
llm_input = get_klse_quarterly_history("5132.KL")

# NEW (v2.0)
from klse_screener import get_klse_quarterly_financials_dict

data = get_klse_quarterly_financials_dict("5132.KL")

# Custom formatting for LLM
def format_quarterly_for_llm(data):
    lines = ["Quarterly Financials:"]
    for q in data["quarterly_data"][:4]:
        lines.append(f"  {q['quarter']}: Revenue={q['revenue']}, EPS={q['eps']}")
    lines.append(f"TTM Revenue: {data['ttm_revenue']}")
    return "\n".join(lines)

llm_input = format_quarterly_for_llm(data)
```

### For Application Users (beatit)

If you're using the library for programmatic access:

- [x] ✅ Already migrated in Phase 3!
- [ ] Test all Magic Formula calculations
- [ ] Verify TTM calculations match previous values
- [ ] Update any direct library calls to use `_dict` functions

## Code Examples

### Magic Formula Calculations

**Before:**
```python
from klse_screener import get_klse_fundamentals

data = get_klse_fundamentals("5132.KL")
market_cap = parse_market_cap(data["market_cap"])  # Manual parsing
```

**After:**
```python
from klse_screener import get_klse_fundamentals_combined

data = get_klse_fundamentals_combined("5132.KL")
market_cap = data["market_cap"]  # Already parsed: "510.0M"
ttm_revenue = data["ttm_revenue"]  # 997200000.0
ebit = data["approx_ebit_ttm"]  # 71100000.0
```

### TTM Calculations

**Before:** Manual calculation required
```python
# User had to calculate TTM manually
quarterly = parse_quarterly_data(html)
ttm = sum(q["revenue"] for q in quarterly[:4])
```

**After:** Automatic TTM included
```python
data = get_klse_quarterly_financials_dict("5132.KL")
ttm_revenue = data["ttm_revenue"]  # Already calculated!
```

### Price History with pandas

**Before:**
```python
# Manual scraping and DataFrame creation
html = scrape_klsescreener(symbol)
df = parse_to_dataframe(html)
```

**After (beatit-specific):**
```python
from app.api.data_sources.klsescreener_fundamentals import fetch_from_klsescreener

df = fetch_from_klsescreener("5132.KL")
# Returns: DataFrame with OHLCV data
```

**After (library-only, pandas-free):**
```python
from klse_screener import scrape_ohlcv_raw

data = scrape_ohlcv_raw("5132.KL", period="30d")
# Returns: List[Dict] - convert to DataFrame yourself if needed
```

## Testing Your Migration

### Unit Tests

```python
import warnings

def test_no_deprecation_warnings():
    """Ensure no deprecation warnings in your code"""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # Your code here
        from klse_screener import get_klse_quarterly_financials_dict
        result = get_klse_quarterly_financials_dict("5132.KL")
        
        # Check no deprecation warnings
        deprecation_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
        assert len(deprecation_warnings) == 0
```

### Integration Tests

```python
def test_magic_formula_data():
    """Verify all required fields for Magic Formula"""
    from klse_screener import get_klse_fundamentals_combined
    
    result = get_klse_fundamentals_combined("5132.KL")
    
    # Required fields
    assert result["market_cap"] is not None
    assert result["pe_ratio"] is not None
    assert result["roe"] is not None
    assert result["ttm_revenue"] is not None
    assert result["ttm_net_profit"] is not None
    assert result["approx_ebit_ttm"] is not None
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'klse_screener'"

```bash
pip install klse-screener-py>=1.3.0
```

### "DeprecationWarning: get_klse_quarterly_history() is deprecated"

Update your code to use the new function:
```python
# OLD
from klse_screener import get_klse_quarterly_history

# NEW
from klse_screener import get_klse_quarterly_financials_dict
```

### "KeyError: 'ttm_revenue'"

Ensure you're using the correct function:
```python
# ❌ Wrong function
data = get_klse_fundamentals("5132.KL")  # May not have TTM

# ✅ Correct function
data = get_klse_fundamentals_combined("5132.KL")  # Has TTM
```

## Getting Help

- **Documentation:** https://github.com/klse-screener-py/README.md
- **Issues:** https://github.com/klse-screener-py/issues
- **Migration Examples:** See `examples/` directory in repository

## Summary

| Task | Action | Deadline |
|------|--------|----------|
| Update quarterly functions | Use `get_klse_quarterly_financials_dict()` | v1.4.0 |
| Update annual functions | Use `get_klse_annual_financials_dict()` | v1.4.0 |
| Test Magic Formula | Verify all fields present | v1.4.0 |
| Remove deprecated imports | Update all `get_klse_*` calls | v2.0.0 |

**Questions?** Open an issue on GitHub or contact the maintainers.
