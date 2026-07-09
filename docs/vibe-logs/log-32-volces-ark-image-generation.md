# TASK-022: 火山引擎豆包文生图集成

**Date**: 2026-07-09
**Owner**: Inner Garden Team
**Branch**: `codex/sync-scripts-to-main`
**Status**: Complete

## Objective

集成火山引擎 Ark API 的豆包文生图模型 (doubao-seedream-5-0-260128)，为 Inner Garden 项目提供替代 DALL-E 的国产图像生成方案，支持水印、2K 分辨率等功能。

## Motivation

项目原有的 AI 图片生成功能仅支持 OpenAI DALL-E，存在以下限制：
- 依赖海外 API，网络访问不稳定
- 成本较高（DALL-E 3: $0.04/张）
- 缺少国产替代方案

火山引擎豆包文生图模型提供：
- 国内网络访问稳定
- 有竞争力的定价
- 支持水印和 2K 分辨率
- OpenAI 兼容的 SDK

## Implementation

### 1. Configuration Changes

**File**: `backend/app/config.py`

Added Volces Ark configuration fields:
```python
volces_api_key: str = getenv("VOLCES_API_KEY", "")
volces_base_url: str = getenv("VOLCES_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
volces_image_model: str = getenv("VOLCES_IMAGE_MODEL", "doubao-seedream-5-0-260128")
```

### 2. AIProvider Extension

**File**: `backend/app/services/ai_provider.py`

Extended `AIProvider` to support `volces` provider:
- Added `"volces"` to provider types
- Added Volces initialization with `ARK_API_KEY` fallback
- Updated `generate_image()` method to support Volces parameters (watermark, 2K size)
- Updated `get_provider()` to set default model for volces

### 3. ImageGenerationService Update

**File**: `backend/app/services/image_generation_service.py`

Updated service to use provider-specific configuration:
- Detects provider from request
- Uses appropriate base URL for each provider
- Passes watermark parameter to AI provider

### 4. Schema Extension

**File**: `backend/app/schemas/images.py`

Extended `ImageGenerationRequest` schema:
```python
provider: Optional[Literal["openai", "volces"]] = "openai"
size: Optional[Literal["1024x1024", "1792x1024", "1024x1792", "2K"]] = "1024x1024"
model: Optional[Literal["dall-e-3", "dall-e-2", "doubao-seedream-5-0-260128"]] = "dall-e-3"
watermark: Optional[bool] = False
```

### 5. Environment Variables Documentation

**File**: `backend/.env.example`

Added configuration documentation:
```bash
# Volces Ark API Key（用于豆包文生图）
VOLCES_API_KEY=your-volces-api-key-here
# 或使用 ARK_API_KEY（兼容环境变量名）
ARK_API_KEY=your-volces-api-key-here

# Volces Ark Base URL（默认北京区域）
VOLCES_BASE_URL=https://ark.cn-beijing.volces.com/api/v3

# Volces 默认图像生成模型
VOLCES_IMAGE_MODEL=doubao-seedream-5-0-260128
```

## Validation

### Backend Build
```bash
cd backend
py -c "from app.main import app; print('Backend imports OK')"
# Result: Backend imports OK
```

### Configuration Verification
```bash
py -c "from app.config import settings; print('volces_base_url:', settings.volces_base_url)"
# Result: volces_base_url: https://ark.cn-beijing.volces.com/api/v3
```

### Schema Verification
```bash
py -c "from app.schemas.images import ImageGenerationRequest; r = ImageGenerationRequest(prompt='Test', provider='volces', model='doubao-seedream-5-0-260128', size='2K', watermark=True); print('Schema OK:', r.provider)"
# Result: Schema OK: volces
```

## API Contract

### Request (POST /api/v1/images/generate)

```json
{
  "prompt": "星际穿越，黑洞，黑洞里冲出一辆快支离破碎的复古列车",
  "provider": "volces",
  "model": "doubao-seedream-5-0-260128",
  "size": "2K",
  "watermark": true,
  "emotion": "calm"
}
```

### Response

```json
{
  "data": {
    "id": 123,
    "image_url": "/uploads/user-ai-abc123.png",
    "prompt_used": "Soft therapeutic watercolor style: ...",
    "revised_prompt": null,
    "model": "doubao-seedream-5-0-260128",
    "size": "2K",
    "generation_time_ms": 3500,
    "created_at": "2026-07-09T12:34:56Z"
  },
  "message": "image_generated"
}
```

## Usage Example

### Frontend API Client

```javascript
// Generate image with Volces Ark
const response = await generateImage({
  prompt: "宁静的水彩风格日落",
  provider: "volces",
  model: "doubao-seedream-5-0-260128",
  size: "2K",
  watermark: true,
  emotion: "calm"
});
```

### Python Backend

```python
from openai import OpenAI
import os

client = OpenAI(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    api_key=os.environ.get("ARK_API_KEY"),
)

response = client.images.generate(
    model="doubao-seedream-5-0-260128",
    prompt="星际穿越，黑洞，黑洞里冲出一辆快支离破碎的复古列车",
    size="2K",
    response_format="url",
    extra_body={"watermark": True},
)

print(response.data[0].url)
```

## Pending Verification

- 实际 API 调用需要配置 `VOLCES_API_KEY`
- 水印功能需要真实 API 调用验证
- 2K 尺寸输出需要真实 API 调用验证

## Files Modified

| File | Operation | Description |
|------|-----------|-------------|
| `backend/app/config.py` | Update | Add volces configuration fields |
| `backend/app/services/ai_provider.py` | Update | Add volces provider support |
| `backend/app/services/image_generation_service.py` | Update | Use provider-specific config |
| `backend/app/schemas/images.py` | Update | Add volces-specific fields |
| `backend/.env.example` | Update | Add volces configuration docs |

## Related Tasks

- TASK-012: AI Image Generation Implementation (original DALL-E integration)

## Notes

- Volces Ark API uses OpenAI-compatible SDK
- Supports both `VOLCES_API_KEY` and `ARK_API_KEY` environment variable names
- Default base URL is Beijing region (`ark.cn-beijing.volces.com`)
- The `watermark` parameter is passed via `extra_body` in the OpenAI SDK
