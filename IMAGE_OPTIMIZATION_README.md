# Image Optimization for Claude API

## Overview

The [`dataset_bundler.py`](dataset_bundler.py) script now includes automatic image optimization to ensure all images comply with Claude API's requirements and recommendations. This optimization happens transparently during the dataset bundling process.

## Why Image Optimization?

### Claude API Limits and Recommendations

Claude API has specific requirements for images:

1. **Hard Limit**: Images must not exceed **5 MB** when base64 encoded
2. **Recommended**: Images should be ≤ **1568px** on any dimension
3. **Optimal**: Images should be ≤ **1.15 megapixels** (~1600 tokens)

### Benefits of Optimization

- **Prevents API Rejections**: Images exceeding 5MB base64 will be rejected
- **Reduces Latency**: Smaller images = faster time-to-first-token
- **Lowers Costs**: Fewer tokens = lower API costs (up to 81% savings)
- **No Performance Loss**: Claude doesn't benefit from extra resolution beyond recommendations

### Cost Impact

**Example from our dataset analysis:**

| Metric | Before Optimization | After Optimization | Savings |
|--------|-------------------|-------------------|---------|
| Average tokens/image | ~8,500 | ~1,600 | 81% |
| Cost per 1K images | ~$25.50 | ~$4.80 | 81% |
| Images exceeding limit | 2 (rejected) | 0 | 100% |

## Configuration Parameters

All optimization parameters are defined in the `IMAGE_OPTIMIZATION_CONFIG` dictionary in [`dataset_bundler.py`](dataset_bundler.py):

```python
IMAGE_OPTIMIZATION_CONFIG = {
    'enabled': True,  # Set to False to disable optimization
    'max_base64_size': 5 * 1024 * 1024,  # 5 MB hard limit
    'recommended_max_dimension': 1568,  # Recommended max dimension
    'recommended_megapixels': 1.15,  # Recommended megapixels
    'optimal_tokens': 1600,  # Optimal token count
    'quality_start': 90,  # Starting JPEG quality
    'quality_min': 70,  # Minimum JPEG quality
    'optimal_sizes': { ... }  # Optimal sizes for common aspect ratios
}
```

### Parameter Details

#### `enabled` (Boolean)
- **Default**: `True`
- **Description**: Master switch for image optimization
- **Usage**: Set to `False` to disable all optimization and just copy images as-is

#### `max_base64_size` (Integer, bytes)
- **Default**: `5242880` (5 MB)
- **Description**: Maximum base64-encoded size allowed by Claude API
- **Note**: This is a hard limit enforced by Claude

#### `recommended_max_dimension` (Integer, pixels)
- **Default**: `1568`
- **Description**: Maximum recommended dimension (width or height)
- **Rationale**: Images larger than this are automatically resized by Claude, adding latency without benefit

#### `recommended_megapixels` (Float)
- **Default**: `1.15`
- **Description**: Maximum recommended total pixels (in millions)
- **Rationale**: Optimal balance between quality and token usage

#### `optimal_tokens` (Integer)
- **Default**: `1600`
- **Description**: Target token count per image
- **Formula**: `tokens = (width × height) / 750`
- **Cost**: ~$4.80 per 1K images at Claude Sonnet 4.5 pricing

#### `quality_start` (Integer, 0-100)
- **Default**: `90`
- **Description**: Initial JPEG quality level for compression
- **Note**: Higher = better quality but larger file size

#### `quality_min` (Integer, 0-100)
- **Default**: `70`
- **Description**: Minimum acceptable JPEG quality
- **Note**: Script will reduce quality to this level if needed to meet size limit

#### `optimal_sizes` (Dictionary)
- **Description**: Optimal dimensions for common aspect ratios
- **Source**: Claude API documentation
- **Purpose**: Images matching these ratios are resized to these exact dimensions for optimal token usage

**Supported Aspect Ratios:**

| Aspect Ratio | Optimal Size | Tokens | Cost/1K Images |
|--------------|--------------|--------|----------------|
| 1:1 (Square) | 1092×1092 | ~1590 | ~$4.80 |
| 3:4 (Portrait) | 951×1268 | ~1605 | ~$4.80 |
| 4:3 (Landscape) | 1268×951 | ~1605 | ~$4.80 |
| 2:3 (Portrait) | 896×1344 | ~1604 | ~$4.80 |
| 3:2 (Landscape) | 1344×896 | ~1604 | ~$4.80 |
| 9:16 (Mobile Portrait) | 819×1456 | ~1588 | ~$4.80 |
| 16:9 (Widescreen) | 1456×819 | ~1588 | ~$4.80 |
| 1:2 (Tall Portrait) | 784×1568 | ~1638 | ~$4.90 |
| 2:1 (Wide Landscape) | 1568×784 | ~1638 | ~$4.90 |

## How Optimization Works

### Process Flow

1. **Check if optimization is needed**
   - Compare image against limits and recommendations
   - Skip optimization if already compliant

2. **Calculate optimal size**
   - Match to standard aspect ratio if within 5% tolerance
   - Otherwise, scale to fit within 1568px and 1.15MP

3. **Resize image**
   - Use high-quality LANCZOS resampling
   - Preserve aspect ratio

4. **Compress to JPEG**
   - Start at quality 90
   - Reduce quality in steps of 5 if needed to meet 5MB limit
   - Stop at minimum quality 70

5. **Save metadata**
   - Record optimization statistics in JSON metadata
   - Track token savings for reporting

### Optimization Decision Tree

```
Image Found
    ↓
Is optimization enabled?
    ├─ No → Copy original
    └─ Yes → Continue
         ↓
Check compliance:
- Base64 size > 5MB?
- Dimension > 1568px?
- Megapixels > 1.15?
    ├─ All No → Copy original (already optimal)
    └─ Any Yes → Optimize
         ↓
Calculate optimal size:
- Match standard aspect ratio?
    ├─ Yes (within 5%) → Use optimal size from table
    └─ No → Scale to 1568px / 1.15MP
         ↓
Resize with LANCZOS
         ↓
Save as JPEG (quality 90)
         ↓
Check base64 size
    ├─ ≤ 5MB → Done
    └─ > 5MB → Reduce quality by 5, repeat
         ↓
Done (quality ≥ 70)
```

## Metadata Tracking

Each optimized image includes optimization metadata in its JSON file:

### For Optimized Images

```json
{
  "image_optimization": {
    "optimized": true,
    "original_tokens": 14270,
    "final_tokens": 1590,
    "tokens_saved": 12680,
    "tokens_saved_percent": 88.9
  }
}
```

### For Already-Optimal Images

```json
{
  "image_optimization": {
    "optimized": false,
    "already_optimal": true,
    "tokens": 200
  }
}
```

## Usage Examples

### Default Usage (Optimization Enabled)

```bash
python dataset_bundler.py
```

All images will be automatically optimized according to Claude's guidelines.

### Disable Optimization

Edit [`dataset_bundler.py`](dataset_bundler.py) and set:

```python
IMAGE_OPTIMIZATION_CONFIG = {
    'enabled': False,
    # ... other settings
}
```

Then run:

```bash
python dataset_bundler.py
```

### Custom Quality Settings

For higher quality (larger files):

```python
IMAGE_OPTIMIZATION_CONFIG = {
    'quality_start': 95,  # Start with higher quality
    'quality_min': 80,    # Don't go below 80
    # ... other settings
}
```

For more aggressive compression:

```python
IMAGE_OPTIMIZATION_CONFIG = {
    'quality_start': 85,  # Start with lower quality
    'quality_min': 60,    # Allow lower minimum
    # ... other settings
}
```

## Verification Tools

### Check Compliance

Before running the bundler, check which images need optimization:

```bash
python check_claude_compliance.py
```

Output shows:
- Images exceeding hard limits (will be rejected)
- Images exceeding recommendations (will work but not optimal)
- Compliant images (already optimal)

### Analyze Costs

Calculate token usage and API costs for all images:

```bash
python analyze_image_costs.py
```

Output includes:
- Token count per image
- Cost per image and per 1K images
- Total costs and savings potential

### Manual Optimization

To optimize a single image for comparison:

```bash
python compress_image_comparison.py
```

Creates:
- Compressed version of the image
- Side-by-side comparison image
- Detailed statistics

## Technical Details

### Token Calculation

Claude uses this formula to calculate image tokens:

```
tokens = (width_px × height_px) / 750
```

**Examples:**
- 1092×1092 = 1,192,464 pixels ÷ 750 = **1,590 tokens**
- 4134×2589 = 10,702,926 pixels ÷ 750 = **14,270 tokens** (8.9× more!)

### Base64 Encoding

Images are base64-encoded before sending to the API, which increases size by ~33%:

```
base64_size ≈ file_size × 1.33
```

**Example:**
- File size: 3.83 MB
- Base64 size: 5.10 MB (exceeds 5 MB limit!)

### Image Formats

- **Input**: Supports JPG, PNG, GIF, BMP, WEBP
- **Output**: Always JPEG (best compression for photos)
- **Conversion**: Automatic, preserves visual quality

### Resampling Method

Uses **LANCZOS** resampling:
- High-quality algorithm
- Preserves sharpness
- Minimal artifacts
- Industry standard for downscaling

## Troubleshooting

### Issue: Images still too large

**Solution**: Reduce `quality_min` parameter:

```python
'quality_min': 60  # or lower
```

### Issue: Images look degraded

**Solution**: Increase quality parameters:

```python
'quality_start': 95,
'quality_min': 80
```

### Issue: Want to keep original sizes

**Solution**: Disable optimization:

```python
'enabled': False
```

Or increase limits (not recommended):

```python
'recommended_max_dimension': 2000,
'recommended_megapixels': 2.0
```

### Issue: Optimization too slow

**Cause**: Base64 encoding for size checking is slow

**Solution**: This is normal. The script checks base64 size to ensure compliance. For large datasets, this adds processing time but ensures no API rejections.

## Best Practices

1. **Always run compliance check first**
   ```bash
   python check_claude_compliance.py
   ```

2. **Use default settings** unless you have specific requirements

3. **Monitor optimization output** during bundling to see which images are optimized

4. **Check metadata** after bundling to verify optimization statistics

5. **Test with a small dataset** before processing large batches

6. **Keep original images** in the source directories (bundler never modifies originals)

## References

- [Claude API Documentation - Vision](https://docs.anthropic.com/claude/docs/vision)
- [Claude API Image Guidelines](https://docs.anthropic.com/claude/docs/vision#image-best-practices)
- [Claude Pricing](https://www.anthropic.com/pricing)

## Support

For issues or questions:
1. Check this README
2. Run verification tools ([`check_claude_compliance.py`](check_claude_compliance.py), [`analyze_image_costs.py`](analyze_image_costs.py))
3. Review optimization metadata in generated JSON files
4. Adjust configuration parameters as needed

---

*Last updated: 2026-01-13*
*Compatible with: Claude Sonnet 4.5 API*
